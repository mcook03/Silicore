from math import sqrt

from engine.risk import make_risk


def _distance(x1, y1, x2, y2):
    return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def _upper_list(values):
    return [str(value).strip().upper() for value in (values or []) if str(value).strip()]


def _matches(net_name, keywords):
    upper = str(net_name or "").strip().upper()
    return any(keyword in upper for keyword in keywords)


def _component_nets(component):
    nets = []
    for pad in getattr(component, "pads", []):
        net_name = str(getattr(pad, "net_name", "")).strip().upper()
        if net_name and net_name not in nets:
            nets.append(net_name)
    return nets


def run_rule(pcb, config):
    risks = []
    rule_config = config.get("rules", {}).get("power_path_realism", {})
    power_config = config.get("power", {})

    high_current_keywords = _upper_list(
        rule_config.get(
            "high_current_net_keywords",
            power_config.get("required_power_nets", []) + ["VIN", "VBUS", "PACK", "BATT", "MOTOR", "12V", "24V"],
        )
    )
    neckdown_ratio_threshold = float(rule_config.get("neckdown_ratio_threshold", 2.5))
    max_high_current_length = float(rule_config.get("max_high_current_length", 40.0))
    converter_cap_radius = float(rule_config.get("converter_cap_radius", 7.0))
    max_high_current_vias = int(rule_config.get("max_high_current_vias", 4))

    capacitors = [component for component in getattr(pcb, "components", []) if str(getattr(component, "ref", "")).upper().startswith("C")]
    regulators = []
    for component in getattr(pcb, "components", []):
        text = f"{getattr(component, 'ref', '')} {getattr(component, 'value', '')} {getattr(component, 'type', '')}".upper()
        if text.startswith("U") and any(keyword in text for keyword in ["REG", "BUCK", "BOOST", "LDO", "PMIC", "CONVERTER"]):
            regulators.append(component)

    for net_name, net in getattr(pcb, "nets", {}).items():
        upper_net = str(net_name).strip().upper()
        if not _matches(upper_net, high_current_keywords):
            continue

        min_width = pcb.min_trace_width_for_net(upper_net)
        max_width = pcb.max_trace_width_for_net(upper_net)
        total_length = pcb.total_trace_length_for_net(upper_net)
        via_count = pcb.via_count_for_net(upper_net)
        components = [component_ref for component_ref, _ in getattr(net, "connections", [])]

        if min_width and max_width and min_width > 0:
            ratio = max_width / min_width
            if ratio > neckdown_ratio_threshold:
                risks.append(
                    make_risk(
                        rule_id="power_path_realism",
                        category="power_integrity",
                        severity="high",
                        message=f"High-current net {upper_net} contains a strong width bottleneck ({min_width:.2f} to {max_width:.2f})",
                        recommendation="Widen the narrow neck-down, shorten the constricted region, or rework the path to reduce resistive and thermal stress.",
                        nets=[upper_net],
                        components=components[:4],
                        metrics={
                            "min_width": round(min_width, 3),
                            "max_width": round(max_width, 3),
                            "ratio": round(ratio, 2),
                            "threshold": neckdown_ratio_threshold,
                        },
                        confidence=0.83,
                        short_title="High-current neck-down bottleneck",
                        fix_priority="high",
                        estimated_impact="high",
                        design_domain="power",
                        why_it_matters="Local bottlenecks in high-current paths can increase voltage drop, heating, and transient impedance.",
                        trigger_condition="A high-current net exceeded the configured width-ratio bottleneck threshold.",
                        threshold_label=f"Maximum neck-down ratio {neckdown_ratio_threshold:.2f}",
                        observed_label=f"Observed width ratio {ratio:.2f}",
                    )
                )

        if total_length > max_high_current_length:
            risks.append(
                make_risk(
                    rule_id="power_path_realism",
                    category="power_integrity",
                    severity="medium",
                    message=f"High-current net {upper_net} uses a long routed path",
                    recommendation="Shorten the power path and tighten the source-to-load loop to reduce parasitic resistance and inductance.",
                    nets=[upper_net],
                    components=components[:4],
                    metrics={
                        "trace_length": round(total_length, 2),
                        "threshold": max_high_current_length,
                    },
                    confidence=0.76,
                    short_title="Long high-current path",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="power",
                    why_it_matters="Longer high-current routes add drop, loop inductance, and dynamic noise in power delivery paths.",
                    trigger_condition="A high-current net exceeded the configured maximum routed-length threshold.",
                    threshold_label=f"Maximum high-current path length {max_high_current_length:.2f} units",
                    observed_label=f"Observed routed length {total_length:.2f} units",
                )
            )

        if via_count > max_high_current_vias:
            risks.append(
                make_risk(
                    rule_id="power_path_realism",
                    category="power_integrity",
                    severity="medium",
                    message=f"High-current net {upper_net} uses many vias ({via_count})",
                    recommendation="Reduce via count or use stronger parallel current return paths on this power route.",
                    nets=[upper_net],
                    components=components[:4],
                    metrics={
                        "via_count": via_count,
                        "threshold": max_high_current_vias,
                    },
                    confidence=0.72,
                    short_title="Power path uses many vias",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="power",
                    why_it_matters="Excessive vias in high-current paths can increase resistance, heat, and transient impedance.",
                    trigger_condition="A high-current net exceeded the configured via-count limit.",
                    threshold_label=f"Maximum high-current vias {max_high_current_vias}",
                    observed_label=f"Observed high-current vias {via_count}",
                )
            )

    for regulator in regulators:
        regulator_nets = set(_component_nets(regulator))
        if not regulator_nets:
            continue
        nearest_cap = None
        for capacitor in capacitors:
            capacitor_nets = set(_component_nets(capacitor))
            if not (regulator_nets & capacitor_nets):
                continue
            distance = _distance(regulator.x, regulator.y, capacitor.x, capacitor.y)
            if nearest_cap is None or distance < nearest_cap[1]:
                nearest_cap = (capacitor, distance)

        if nearest_cap is None or nearest_cap[1] > converter_cap_radius:
            risks.append(
                make_risk(
                    rule_id="power_path_realism",
                    category="power_integrity",
                    severity="medium",
                    message=f"Regulator or converter {regulator.ref} lacks a nearby shared capacitor network",
                    recommendation="Move input or output capacitors closer to the converter power pins so current loops stay compact.",
                    components=[regulator.ref] + ([nearest_cap[0].ref] if nearest_cap else []),
                    nets=sorted(list(regulator_nets))[:4],
                    metrics={
                        "nearest_shared_cap_distance": round(nearest_cap[1], 2) if nearest_cap else None,
                        "threshold": converter_cap_radius,
                    },
                    confidence=0.75,
                    short_title="Converter capacitor placement is weak",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="power",
                    why_it_matters="Converters rely on tight capacitor placement to keep di/dt loops small and power noise under control.",
                    trigger_condition="A regulator-like component had no nearby shared capacitor inside the configured converter-cap radius.",
                    threshold_label=f"Maximum shared capacitor radius {converter_cap_radius:.2f} units",
                    observed_label=f"Observed nearest shared capacitor distance {nearest_cap[1]:.2f} units" if nearest_cap else "Observed shared capacitor distance: none",
                )
            )

    return risks
