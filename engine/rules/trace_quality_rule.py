from engine.risk import make_risk


def run_rule(pcb, config):
    risks = []

    for net_name, net in pcb.nets.items():
        traces = pcb.get_traces_by_net(net_name)
        if not traces:
            continue

        total_length = pcb.total_trace_length_for_net(net_name)
        min_width = pcb.min_trace_width_for_net(net_name)

        if total_length > 120.0:
            risks.append(
                make_risk(
                    rule_id="trace_quality",
                    category="signal_integrity",
                    severity="medium",
                    message=f"Net {net_name} has a long total routed trace length ({total_length:.2f} units)",
                    recommendation="Review routing topology and shorten critical signal traces where practical.",
                    nets=[net_name],
                    metrics={
                        "trace_length": total_length,
                        "threshold": 120.0,
                    },
                    confidence=0.78,
                    short_title="Long routed signal length",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="signal",
                )
            )

        if min_width is not None and min_width < 0.15:
            risks.append(
                make_risk(
                    rule_id="trace_quality",
                    category="manufacturing",
                    severity="medium",
                    message=f"Net {net_name} contains a very narrow trace ({min_width:.2f})",
                    recommendation="Review manufacturability limits and increase trace width if the design rules require it.",
                    nets=[net_name],
                    metrics={
                        "min_trace_width": min_width,
                        "threshold": 0.15,
                    },
                    confidence=0.83,
                    short_title="Very narrow trace",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="layout",
                )
            )

    return risks