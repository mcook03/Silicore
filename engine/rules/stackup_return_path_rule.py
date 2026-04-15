from math import sqrt

from engine.risk import make_risk


def _distance(x1, y1, x2, y2):
    return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def _upper_list(values):
    return [str(value).strip().upper() for value in (values or []) if str(value).strip()]


def _matches(net_name, keywords):
    upper = str(net_name or "").strip().upper()
    return any(keyword in upper for keyword in keywords)


def run_rule(pcb, config):
    risks = []
    rule_config = config.get("rules", {}).get("stackup_return_path", {})
    signal_config = config.get("signal", {})
    power_config = config.get("power", {})

    critical_keywords = _upper_list(
        rule_config.get(
            "critical_net_keywords",
            signal_config.get("critical_nets", []) + ["USB", "DDR", "PCIE", "ETH", "CLK", "MIPI", "CAN"],
        )
    )
    ground_keywords = _upper_list(power_config.get("required_ground_nets", ["GND", "GROUND"]))
    max_signal_layers = int(rule_config.get("max_signal_layers", 2))
    signal_via_ground_radius = float(rule_config.get("signal_via_ground_radius", 3.5))
    max_two_layer_critical_length = float(rule_config.get("max_two_layer_critical_length", 28.0))

    copper_layer_count = len([layer for layer in getattr(pcb, "layers", set()) if ".CU" in str(layer).upper()])

    for net_name, net in getattr(pcb, "nets", {}).items():
        upper_net = str(net_name).strip().upper()
        if not _matches(upper_net, critical_keywords):
            continue

        layer_count = pcb.layer_count_for_net(upper_net)
        total_length = pcb.total_trace_length_for_net(upper_net)
        vias = pcb.get_vias_by_net(upper_net)
        components = [component_ref for component_ref, _ in getattr(net, "connections", [])]

        if layer_count > max_signal_layers:
            risks.append(
                make_risk(
                    rule_id="stackup_return_path",
                    category="stackup_return_path",
                    severity="medium",
                    message=f"Critical net {upper_net} spans many copper layers ({layer_count})",
                    recommendation="Keep sensitive nets referenced to a more consistent layer pair or simplify the routing path across the stackup.",
                    nets=[upper_net],
                    components=components[:4],
                    metrics={
                        "layer_count": layer_count,
                        "threshold": max_signal_layers,
                    },
                    confidence=0.79,
                    short_title="Critical routing spans too many layers",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="stackup",
                    why_it_matters="Each extra routing layer transition increases the chance of reference changes and return-current discontinuities.",
                    trigger_condition="A critical net exceeded the configured maximum copper-layer span.",
                    threshold_label=f"Maximum signal layers {max_signal_layers}",
                    observed_label=f"Observed signal layers {layer_count}",
                )
            )

        if copper_layer_count <= 2 and total_length > max_two_layer_critical_length:
            risks.append(
                make_risk(
                    rule_id="stackup_return_path",
                    category="stackup_return_path",
                    severity="medium",
                    message=f"Critical net {upper_net} is long for a two-layer style stackup",
                    recommendation="Review whether this board class needs a stronger reference-plane strategy or a stackup with better return-path support.",
                    nets=[upper_net],
                    components=components[:4],
                    metrics={
                        "trace_length": round(total_length, 2),
                        "threshold": max_two_layer_critical_length,
                        "copper_layers": copper_layer_count,
                    },
                    confidence=0.7,
                    short_title="Limited stackup for critical routing",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="stackup",
                    why_it_matters="Long critical routes on a minimal stackup are harder to keep well referenced and more sensitive to return-path problems.",
                    trigger_condition="A critical net exceeded the two-layer critical-length threshold while board copper layers stayed limited.",
                    threshold_label=f"Maximum two-layer critical length {max_two_layer_critical_length:.2f} units",
                    observed_label=f"Observed critical routed length {total_length:.2f} units",
                )
            )

        unsupported_vias = 0
        for signal_via in vias:
            nearby_ground = False
            for ground_via in getattr(pcb, "vias", []):
                if not _matches(getattr(ground_via, "net_name", ""), ground_keywords):
                    continue
                if _distance(signal_via.x, signal_via.y, ground_via.x, ground_via.y) <= signal_via_ground_radius:
                    nearby_ground = True
                    break
            if not nearby_ground:
                unsupported_vias += 1

        if unsupported_vias:
            risks.append(
                make_risk(
                    rule_id="stackup_return_path",
                    category="stackup_return_path",
                    severity="high",
                    message=f"Critical net {upper_net} changes layers without nearby ground-return stitching",
                    recommendation="Place ground stitching vias near sensitive transitions so return current does not need to detour around the layer change.",
                    nets=[upper_net],
                    components=components[:4],
                    metrics={
                        "unsupported_vias": unsupported_vias,
                        "signal_via_ground_radius": signal_via_ground_radius,
                    },
                    confidence=0.84,
                    short_title="Return-path support missing at signal transitions",
                    fix_priority="high",
                    estimated_impact="high",
                    design_domain="stackup",
                    why_it_matters="Signal vias without nearby return stitching can break reference continuity and worsen both signal integrity and EMI.",
                    trigger_condition="Critical-net vias were found outside the configured ground-stitch support radius.",
                    threshold_label=f"Ground-stitch support radius {signal_via_ground_radius:.2f} units",
                    observed_label=f"Observed unsupported signal vias {unsupported_vias}",
                )
            )

    return risks
