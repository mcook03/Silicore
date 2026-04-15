from engine.risk import make_risk


def _upper_list(values):
    return [str(value).strip().upper() for value in (values or []) if str(value).strip()]


def _net_matches(net_name, keywords):
    upper = str(net_name or "").strip().upper()
    return any(keyword in upper for keyword in keywords)


def run_rule(pcb, config):
    risks = []
    rule_config = config.get("rules", {}).get("current_density", {})
    power_config = config.get("power", {})

    high_current_keywords = _upper_list(
        rule_config.get(
            "high_current_net_keywords",
            power_config.get("required_power_nets", ["VIN", "VBUS", "VCC", "VBAT", "5V", "12V"]) + ["SW", "PHASE", "PACK", "BATT"],
        )
    )
    min_high_current_width = float(rule_config.get("min_high_current_width", 0.7))
    max_bottleneck_length = float(rule_config.get("max_bottleneck_length", 24.0))
    neckdown_ratio_threshold = float(rule_config.get("neckdown_ratio_threshold", 2.5))
    max_bottleneck_vias = int(rule_config.get("max_bottleneck_vias", 3))

    for net_name in getattr(pcb, "nets", {}).keys():
        upper_net = str(net_name or "").strip().upper()
        if not upper_net or not _net_matches(upper_net, high_current_keywords):
            continue

        total_length = pcb.total_trace_length_for_net(upper_net)
        min_width = pcb.min_trace_width_for_net(upper_net)
        max_width = pcb.max_trace_width_for_net(upper_net)
        via_count = pcb.via_count_for_net(upper_net)
        involved_components = [ref for ref, _ in getattr(pcb.nets.get(upper_net), "connections", [])]

        if min_width is not None and min_width < min_high_current_width and total_length > max_bottleneck_length:
            risks.append(
                make_risk(
                    rule_id="current_density",
                    category="power_integrity",
                    severity="high",
                    message=f"High-current net {upper_net} bottlenecks through a narrow copper section",
                    recommendation="Widen the narrow neck-down, shorten the high-current route, or add parallel copper/plane support to reduce current-density and voltage-drop pressure.",
                    components=involved_components[:4],
                    nets=[upper_net],
                    metrics={
                        "min_width": round(min_width, 3),
                        "recommended_width": round(min_high_current_width, 3),
                        "trace_length": round(total_length, 2),
                    },
                    confidence=0.86,
                    short_title="High-current copper bottleneck",
                    fix_priority="high",
                    estimated_impact="high",
                    design_domain="power_path",
                    why_it_matters="Narrow copper in a long high-current path increases resistive loss, heating, and voltage-drop risk.",
                    trigger_condition="A high-current net used a minimum width below the configured current-density limit over a materially long route.",
                    threshold_label=f"Minimum high-current width {min_high_current_width:.2f} units with maximum bottleneck length {max_bottleneck_length:.2f} units",
                    observed_label=f"Observed minimum width {min_width:.2f} units over {total_length:.2f} routed units",
                )
            )

        if min_width is not None and max_width is not None and min_width > 0:
            width_ratio = max_width / min_width
            if width_ratio >= neckdown_ratio_threshold:
                risks.append(
                    make_risk(
                        rule_id="current_density",
                        category="power_integrity",
                        severity="medium",
                        message=f"High-current net {upper_net} shows a strong width neck-down that may concentrate current density",
                        recommendation="Keep high-current copper width more consistent through the load path and avoid abrupt neck-down transitions near sources, loads, or connectors.",
                        components=involved_components[:4],
                        nets=[upper_net],
                        metrics={
                            "width_ratio": round(width_ratio, 2),
                            "min_width": round(min_width, 3),
                            "max_width": round(max_width, 3),
                        },
                        confidence=0.79,
                        short_title="Inconsistent current-path copper width",
                        fix_priority="medium",
                        estimated_impact="moderate",
                        design_domain="power_path",
                        why_it_matters="Abrupt width changes create current bottlenecks and can localize heating or parasitic loss in power paths.",
                        trigger_condition="A high-current net exceeded the configured copper neck-down ratio.",
                        threshold_label=f"Maximum neck-down ratio {neckdown_ratio_threshold:.2f}",
                        observed_label=f"Observed width ratio {width_ratio:.2f}",
                    )
                )

        if via_count > max_bottleneck_vias and min_width is not None and min_width < min_high_current_width * 1.15:
            risks.append(
                make_risk(
                    rule_id="current_density",
                    category="power_integrity",
                    severity="medium",
                    message=f"High-current net {upper_net} relies on many transitions through a narrow path",
                    recommendation="Reduce unnecessary layer changes in the high-current route or add stronger parallel current-return support across the transitions.",
                    components=involved_components[:4],
                    nets=[upper_net],
                    metrics={
                        "via_count": via_count,
                        "max_bottleneck_vias": max_bottleneck_vias,
                        "min_width": round(min_width, 3),
                    },
                    confidence=0.74,
                    short_title="Transition-heavy high-current route",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="power_path",
                    why_it_matters="Many transitions in a narrow high-current path can add parasitic resistance and inductance while concentrating heating risk.",
                    trigger_condition="A high-current net exceeded the configured transition count while also staying near the narrow-width limit.",
                    threshold_label=f"Maximum transition count {max_bottleneck_vias}",
                    observed_label=f"Observed transition count {via_count}",
                )
            )

    return risks
