from math import sqrt

from engine.risk import make_risk


def _distance(x1, y1, x2, y2):
    return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def _upper_list(values):
    return [str(value).strip().upper() for value in (values or []) if str(value).strip()]


def _net_matches(net_name, keywords):
    upper = str(net_name or "").strip().upper()
    return any(keyword in upper for keyword in keywords)


def _sensitive_components(pcb, keywords):
    items = []
    for component in getattr(pcb, "components", []):
        text = f"{getattr(component, 'ref', '')} {getattr(component, 'value', '')} {getattr(component, 'type', '')}".upper()
        if any(keyword in text for keyword in keywords):
            items.append(component)
    return items


def _nearest_ground_via_distance(pcb, x, y, ground_keywords):
    best = None
    for via in getattr(pcb, "vias", []):
        if not _net_matches(getattr(via, "net_name", ""), ground_keywords):
            continue
        distance = _distance(x, y, via.x, via.y)
        if best is None or distance < best:
            best = distance
    return best


def run_rule(pcb, config):
    risks = []
    rule_config = config.get("rules", {}).get("emi_emc", {})
    signal_config = config.get("signal", {})
    power_config = config.get("power", {})

    noisy_keywords = _upper_list(
        rule_config.get(
            "noisy_net_keywords",
            ["SW", "PHASE", "BOOT", "PWM", "CLK", "USB", "ETH", "DDR", "PCIE", "CAN"],
        )
    )
    sensitive_keywords = _upper_list(
        rule_config.get(
            "sensitive_component_keywords",
            ["ADC", "DAC", "REF", "XTAL", "OSC", "RF", "ANT", "SENSOR", "LNA", "AMP", "OPAMP"],
        )
    )
    ground_keywords = _upper_list(power_config.get("required_ground_nets", ["GND", "GROUND"]))
    critical_keywords = _upper_list(signal_config.get("critical_nets", [])) + noisy_keywords

    max_switch_trace_length = float(rule_config.get("max_switch_trace_length", 18.0))
    sensitive_keepout = float(rule_config.get("sensitive_keepout", 6.0))
    return_via_radius = float(rule_config.get("return_via_radius", 3.0))
    max_loop_length = float(rule_config.get("max_loop_length", 45.0))

    sensitive_components = _sensitive_components(pcb, sensitive_keywords)

    for net_name, net in getattr(pcb, "nets", {}).items():
        upper_net = str(net_name).strip().upper()
        if not upper_net:
            continue

        total_length = pcb.total_trace_length_for_net(upper_net)
        layer_count = pcb.layer_count_for_net(upper_net)
        via_count = pcb.via_count_for_net(upper_net)
        traces = pcb.get_traces_by_net(upper_net)
        involved_components = [component_ref for component_ref, _ in getattr(net, "connections", [])]

        is_fast_or_noisy = _net_matches(upper_net, critical_keywords)
        is_switching_power = _net_matches(upper_net, ["SW", "PHASE", "BOOT", "PWM", "VIN", "VBUS", "VCC"])

        if is_fast_or_noisy and total_length > max_switch_trace_length and layer_count > 1:
            unsupported_vias = 0
            for via in pcb.get_vias_by_net(upper_net):
                nearest_ground = _nearest_ground_via_distance(pcb, via.x, via.y, ground_keywords)
                if nearest_ground is None or nearest_ground > return_via_radius:
                    unsupported_vias += 1

            if unsupported_vias:
                risks.append(
                    make_risk(
                        rule_id="emi_emc",
                        category="emi_emc",
                        severity="high",
                        message=f"Fast or noisy net {upper_net} changes layers without nearby return-path stitching support",
                        recommendation="Add nearby ground stitching vias or keep the route on a better contained reference path to reduce return-current disruption.",
                        nets=[upper_net],
                        components=involved_components[:4],
                        metrics={
                            "unsupported_vias": unsupported_vias,
                            "return_via_radius": return_via_radius,
                            "trace_length": round(total_length, 2),
                        },
                        confidence=0.82,
                        short_title="Weak EMC containment across layer changes",
                        fix_priority="high",
                        estimated_impact="high",
                        design_domain="emi",
                        why_it_matters="Layer transitions without nearby ground stitching can force return current to spread and increase EMI.",
                        trigger_condition="A fast or noisy net exceeded the switch-trace threshold and changed layers without nearby ground-via support.",
                        threshold_label=f"Maximum unsupported transition radius {return_via_radius:.2f} units",
                        observed_label=f"Observed unsupported transitions {unsupported_vias}",
                    )
                )

        if is_fast_or_noisy and traces and sensitive_components:
            nearest_sensitive = None
            for component in sensitive_components:
                for segment in traces:
                    midpoint_x = (segment.x1 + segment.x2) / 2.0
                    midpoint_y = (segment.y1 + segment.y2) / 2.0
                    distance = _distance(midpoint_x, midpoint_y, component.x, component.y)
                    if nearest_sensitive is None or distance < nearest_sensitive[1]:
                        nearest_sensitive = (component, distance)

            if nearest_sensitive and nearest_sensitive[1] < sensitive_keepout:
                component = nearest_sensitive[0]
                risks.append(
                    make_risk(
                        rule_id="emi_emc",
                        category="emi_emc",
                        severity="medium",
                        message=f"Noisy net {upper_net} routes close to sensitive circuitry near {component.ref}",
                        recommendation="Increase separation, improve shielding/reference continuity, or move the sensitive analog, RF, or clock circuitry away from the aggressor route.",
                        nets=[upper_net],
                        components=[component.ref] + involved_components[:3],
                        metrics={
                            "distance_to_sensitive_region": round(nearest_sensitive[1], 2),
                            "keepout": sensitive_keepout,
                        },
                        confidence=0.78,
                        short_title="Aggressor near sensitive circuitry",
                        fix_priority="medium",
                        estimated_impact="moderate",
                        design_domain="emi",
                        why_it_matters="Fast or noisy traces placed close to analog, RF, or timing-sensitive circuitry can increase conducted and radiated interference.",
                        trigger_condition="A noisy route midpoint fell inside the configured sensitive-circuit keepout window.",
                        threshold_label=f"Minimum sensitive keepout {sensitive_keepout:.2f} units",
                        observed_label=f"Observed nearest sensitive distance {nearest_sensitive[1]:.2f} units",
                    )
                )

        if is_switching_power and total_length > max_loop_length and len(involved_components) <= 3:
            risks.append(
                make_risk(
                    rule_id="emi_emc",
                    category="emi_emc",
                    severity="medium",
                    message=f"Switching or power net {upper_net} forms a long exposed loop path",
                    recommendation="Tighten the converter current loop, shorten the route, and keep the return path adjacent to reduce loop area and EMI.",
                    nets=[upper_net],
                    components=involved_components[:4],
                    metrics={
                        "trace_length": round(total_length, 2),
                        "max_loop_length": max_loop_length,
                        "via_count": via_count,
                    },
                    confidence=0.74,
                    short_title="Large switching loop area",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="emi",
                    why_it_matters="Large current loops increase magnetic field radiation and make noisy power stages harder to contain.",
                    trigger_condition="A switching or power-oriented net exceeded the configured loop-length threshold.",
                    threshold_label=f"Maximum switching loop length {max_loop_length:.2f} units",
                    observed_label=f"Observed routed length {total_length:.2f} units",
                )
            )

    return risks
