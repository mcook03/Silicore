from engine.risk import make_risk
from engine.net_utils import is_power_net


def run_rule(pcb, config):
    risks = []
    rule_config = config["rules"]["power_rail"]

    min_connections = rule_config["min_connections"]
    max_trace_length = rule_config["max_trace_length"]
    min_trace_width = rule_config["min_trace_width"]
    max_via_count = rule_config["max_via_count"]
    power_net_keywords = rule_config["power_net_keywords"]

    for net_name, net in pcb.nets.items():
        if not is_power_net(net_name, power_net_keywords):
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
                    why_it_matters="Weak connectivity on a power rail can indicate missing load coverage or incomplete distribution paths.",
                    suggested_actions=[
                        "Verify intended loads are attached to this power net.",
                        "Check for missing net assignments or disconnected pads.",
                        "Confirm power reaches all required components.",
                    ],
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
                    why_it_matters="Long power paths can increase resistance, voltage drop, and noise susceptibility.",
                    suggested_actions=[
                        "Shorten the route between source and loads.",
                        "Move the regulator or source closer to major loads.",
                        "Review distribution topology for unnecessary detours.",
                    ],
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
                    why_it_matters="Narrow power traces can overheat and create avoidable IR drop under load.",
                    suggested_actions=[
                        "Increase trace width on the critical power segment.",
                        "Check expected current draw for this rail.",
                        "Consider copper pours for heavier current paths.",
                    ],
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
                    why_it_matters="Excessive via transitions can increase path impedance and reduce power-delivery quality.",
                    suggested_actions=[
                        "Flatten the route where possible.",
                        "Reduce unnecessary layer changes.",
                        "Keep critical power paths direct and wide.",
                    ],
                )
            )

    return risks