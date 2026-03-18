from engine.risk import make_risk

POWER_NET_KEYWORDS = {"VCC", "VIN", "VBAT", "5V", "3V3", "12V", "1V8"}


def run_rule(pcb, config):
    risks = []
    rule_config = config["rules"]["power_rail"]

    min_connections = rule_config["min_connections"]
    max_trace_length = rule_config["max_trace_length"]
    min_trace_width = rule_config["min_trace_width"]
    max_via_count = rule_config["max_via_count"]

    for net_name, net in pcb.nets.items():
        upper_name = net_name.upper()

        if not any(keyword in upper_name for keyword in POWER_NET_KEYWORDS):
            continue

        connection_count = len([conn for conn in net.connections if conn[0]])
        total_trace_length = pcb.total_trace_length_for_net(net_name)
        min_width = pcb.min_trace_width_for_net(net_name)
        via_count = len(pcb.get_vias_by_net(net_name))

        if connection_count < min_connections:
            risks.append(
                make_risk(
                    rule_id="power_rail",
                    category="power_integrity",
                    severity="medium",
                    message=f"Power net {net_name} appears weakly connected with only {connection_count} mapped connection(s)",
                    recommendation="Verify the power rail reaches all required loads and that its connectivity is correctly defined.",
                    nets=[net_name],
                    metrics={
                        "connection_count": connection_count,
                        "min_connections": min_connections,
                    },
                    confidence=0.72,
                    short_title="Weak power rail connectivity",
                    fix_priority="high",
                    estimated_impact="high",
                    design_domain="power",
                )
            )

        if total_trace_length > max_trace_length and total_trace_length > 0:
            risks.append(
                make_risk(
                    rule_id="power_rail",
                    category="power_integrity",
                    severity="high",
                    message=f"Power net {net_name} has excessive routed length ({total_trace_length:.2f} units)",
                    recommendation="Reduce power path length or improve distribution topology to lower impedance and voltage drop risk.",
                    nets=[net_name],
                    metrics={
                        "trace_length": total_trace_length,
                        "max_trace_length": max_trace_length,
                    },
                    confidence=0.84,
                    short_title="Excessive power rail length",
                    fix_priority="high",
                    estimated_impact="high",
                    design_domain="power",
                )
            )

        if min_width is not None and min_width < min_trace_width:
            risks.append(
                make_risk(
                    rule_id="power_rail",
                    category="power_integrity",
                    severity="high",
                    message=f"Power net {net_name} uses a narrow trace width ({min_width:.2f})",
                    recommendation="Increase power trace width to reduce resistance, heating, and voltage drop.",
                    nets=[net_name],
                    metrics={
                        "min_trace_width": min_width,
                        "required_min_trace_width": min_trace_width,
                    },
                    confidence=0.9,
                    short_title="Narrow power trace",
                    fix_priority="high",
                    estimated_impact="high",
                    design_domain="power",
                )
            )

        if via_count > max_via_count:
            risks.append(
                make_risk(
                    rule_id="power_rail",
                    category="power_integrity",
                    severity="medium",
                    message=f"Power net {net_name} uses many vias ({via_count}) which may increase impedance",
                    recommendation="Reduce unnecessary via transitions on critical power nets where possible.",
                    nets=[net_name],
                    metrics={
                        "via_count": via_count,
                        "max_via_count": max_via_count,
                    },
                    confidence=0.7,
                    short_title="Too many power-net vias",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="power",
                )
            )

    return risks