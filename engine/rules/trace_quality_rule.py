from engine.risk import make_risk
from engine.net_utils import is_excluded_net


def run_rule(pcb, config):
    risks = []
    rule_config = config.get("rules", {}).get("trace_quality", {})

    max_signal_trace_length = float(rule_config.get("max_signal_trace_length", 60.0))
    min_general_trace_width = float(rule_config.get("min_general_trace_width", 0.15))
    excluded_net_keywords = rule_config.get(
        "excluded_net_keywords",
        ["GND", "GROUND", "VCC", "VIN", "VBAT", "3V3", "5V", "12V", "VDD"],
    )

    for net_name, net in getattr(pcb, "nets", {}).items():
        if is_excluded_net(net_name, excluded_net_keywords):
            continue

        traces = pcb.get_traces_by_net(net_name)
        if not traces:
            continue

        total_length = pcb.total_trace_length_for_net(net_name)
        min_width = pcb.min_trace_width_for_net(net_name)

        if total_length > max_signal_trace_length:
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
                        "threshold": max_signal_trace_length,
                    },
                    confidence=0.78,
                    short_title="Long routed signal length",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="signal",
                    why_it_matters="Long signal routes can worsen noise sensitivity, delay, and routing quality on important nets.",
                    suggested_actions=[
                        "Shorten the overall routing path.",
                        "Reduce unnecessary detours.",
                        "Review whether this net should be treated as timing- or noise-sensitive.",
                    ],
                    trigger_condition="Signal-net routed length exceeded the configured maximum signal trace threshold.",
                    threshold_label=f"Maximum signal trace length {max_signal_trace_length:.2f} units",
                    observed_label=f"Observed trace length {total_length:.2f} units",
                )
            )

        if min_width is not None and min_width < min_general_trace_width:
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
                        "threshold": min_general_trace_width,
                    },
                    confidence=0.83,
                    short_title="Very narrow trace",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="layout",
                    why_it_matters="Very narrow traces can be harder to manufacture reliably and may reduce yield margin.",
                    suggested_actions=[
                        "Increase trace width if routing space allows.",
                        "Check board-house minimum trace capability.",
                        "Review whether this narrow section is intentional.",
                    ],
                    trigger_condition="Signal trace width fell below the configured minimum manufacturable width threshold.",
                    threshold_label=f"Minimum general trace width {min_general_trace_width:.2f}",
                    observed_label=f"Observed trace width {min_width:.2f}",
                )
            )

    return risks
