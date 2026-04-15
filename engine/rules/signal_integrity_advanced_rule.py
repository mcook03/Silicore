from math import sqrt

from engine.net_utils import is_critical_signal_net, is_excluded_net
from engine.risk import make_risk


def _distance(x1, y1, x2, y2):
    return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def _safe_upper_list(values):
    return [str(value).strip().upper() for value in (values or []) if str(value).strip()]


def _segment_angle_similarity(segment_a, segment_b):
    dx_a = segment_a.x2 - segment_a.x1
    dy_a = segment_a.y2 - segment_a.y1
    dx_b = segment_b.x2 - segment_b.x1
    dy_b = segment_b.y2 - segment_b.y1

    mag_a = sqrt((dx_a ** 2) + (dy_a ** 2))
    mag_b = sqrt((dx_b ** 2) + (dy_b ** 2))
    if mag_a == 0 or mag_b == 0:
        return 0.0

    return abs(((dx_a * dx_b) + (dy_a * dy_b)) / (mag_a * mag_b))


def _segment_midpoint_distance(segment_a, segment_b):
    ax = (segment_a.x1 + segment_a.x2) / 2
    ay = (segment_a.y1 + segment_a.y2) / 2
    bx = (segment_b.x1 + segment_b.x2) / 2
    by = (segment_b.y1 + segment_b.y2) / 2
    return _distance(ax, ay, bx, by)


def _component_positions_for_net(pcb, net_name):
    positions = []
    for component_ref, _ in getattr(pcb.nets.get(net_name), "connections", []):
        component = pcb.get_component(component_ref)
        if component is None:
            continue
        positions.append((component.ref, component.x, component.y))
    return positions


def _max_direct_distance(positions):
    max_distance = 0.0
    pair = None
    for index, left in enumerate(positions):
        for right in positions[index + 1:]:
            distance = _distance(left[1], left[2], right[1], right[2])
            if distance > max_distance:
                max_distance = distance
                pair = (left[0], right[0])
    return max_distance, pair


def run_rule(pcb, config):
    risks = []
    rule_config = config.get("rules", {}).get("signal_integrity_advanced", {})
    signal_config = config.get("signal", {})
    power_config = config.get("power", {})

    configured_critical_keywords = _safe_upper_list(signal_config.get("critical_nets", []))
    default_critical_keywords = ["CLK", "USB", "DDR", "PCIE", "MIPI", "ETH", "CAN", "SCL", "SDA", "DP", "DN"]
    critical_net_keywords = _safe_upper_list(
        rule_config.get(
            "critical_net_keywords",
            configured_critical_keywords + default_critical_keywords,
        )
    )
    excluded_net_keywords = _safe_upper_list(
        rule_config.get(
            "excluded_net_keywords",
            signal_config.get(
                "excluded_net_keywords",
                power_config.get("required_power_nets", []) + power_config.get("required_ground_nets", []),
            ),
        )
    )

    max_signal_vias = int(rule_config.get("max_signal_vias", 2))
    width_ratio_threshold = float(rule_config.get("width_ratio_threshold", 2.2))
    detour_ratio_threshold = float(rule_config.get("detour_ratio_threshold", 1.8))
    stub_length_threshold = float(rule_config.get("stub_length_threshold", 12.0))
    crosstalk_spacing_threshold = float(rule_config.get("crosstalk_spacing_threshold", 2.5))
    crosstalk_parallel_similarity = float(rule_config.get("crosstalk_parallel_similarity", 0.96))
    crosstalk_parallel_length = float(rule_config.get("crosstalk_parallel_length", 8.0))

    candidate_nets = []
    for net_name, net in getattr(pcb, "nets", {}).items():
        upper_net = str(net_name).strip().upper()
        if not upper_net:
            continue
        if is_excluded_net(upper_net, excluded_net_keywords):
            continue
        if is_critical_signal_net(upper_net, critical_net_keywords):
            candidate_nets.append((upper_net, net))

    for net_name, net in candidate_nets:
        traces = pcb.get_traces_by_net(net_name)
        if not traces:
            continue

        min_width = pcb.min_trace_width_for_net(net_name)
        max_width = pcb.max_trace_width_for_net(net_name)
        via_count = pcb.via_count_for_net(net_name)
        total_length = pcb.total_trace_length_for_net(net_name)
        positions = _component_positions_for_net(pcb, net_name)
        direct_distance, endpoint_pair = _max_direct_distance(positions)
        connection_count = len(getattr(net, "connections", []) or [])

        if min_width and max_width and min_width > 0:
            ratio = max_width / min_width
            if ratio > width_ratio_threshold:
                risks.append(
                    make_risk(
                        rule_id="signal_integrity_advanced",
                        category="signal_integrity",
                        severity="high",
                        message=f"Critical net {net_name} uses inconsistent trace widths ({min_width:.2f} to {max_width:.2f})",
                        recommendation="Keep critical routing widths more consistent so impedance changes and reflections are reduced.",
                        nets=[net_name],
                        components=list(endpoint_pair or []),
                        metrics={
                            "min_trace_width": round(min_width, 3),
                            "max_trace_width": round(max_width, 3),
                            "ratio": round(ratio, 2),
                            "threshold": width_ratio_threshold,
                        },
                        confidence=0.88,
                        short_title="Critical-net width inconsistency",
                        fix_priority="high",
                        estimated_impact="high",
                        design_domain="signal",
                        why_it_matters="Large trace-width changes on critical nets can shift impedance and increase reflection risk.",
                        trigger_condition="Critical-net width ratio exceeded the configured signal-integrity width consistency threshold.",
                        threshold_label=f"Maximum width ratio {width_ratio_threshold:.2f}",
                        observed_label=f"Observed width ratio {ratio:.2f}",
                    )
                )

        if via_count > max_signal_vias:
            risks.append(
                make_risk(
                    rule_id="signal_integrity_advanced",
                    category="signal_integrity",
                    severity="medium",
                    message=f"Critical net {net_name} uses many via transitions ({via_count})",
                    recommendation="Reduce layer transitions on sensitive nets where possible to improve continuity and reduce impedance discontinuities.",
                    nets=[net_name],
                    metrics={
                        "via_count": via_count,
                        "threshold": max_signal_vias,
                    },
                    confidence=0.84,
                    short_title="Excessive signal vias",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="signal",
                    why_it_matters="Each via transition can add discontinuity and degrade high-speed or timing-sensitive signals.",
                    trigger_condition="Critical-net via count exceeded the configured maximum transition threshold.",
                    threshold_label=f"Maximum signal vias {max_signal_vias}",
                    observed_label=f"Observed signal vias {via_count}",
                )
            )

        if direct_distance > 0:
            detour_ratio = total_length / direct_distance
            if detour_ratio > detour_ratio_threshold:
                risks.append(
                    make_risk(
                        rule_id="signal_integrity_advanced",
                        category="layout_quality",
                        severity="medium",
                        message=f"Critical net {net_name} takes a long routed detour ({total_length:.2f} vs {direct_distance:.2f} direct)",
                        recommendation="Review the routing path and remove unnecessary detours on this critical net.",
                        nets=[net_name],
                        components=list(endpoint_pair or []),
                        metrics={
                            "trace_length": round(total_length, 2),
                            "direct_distance": round(direct_distance, 2),
                            "ratio": round(detour_ratio, 2),
                            "threshold": detour_ratio_threshold,
                        },
                        confidence=0.8,
                        short_title="Critical-net routing detour",
                        fix_priority="medium",
                        estimated_impact="moderate",
                        design_domain="layout",
                        why_it_matters="Long detours increase delay, noise sensitivity, and route inconsistency on important nets.",
                        trigger_condition="Critical-net routed length exceeded the configured detour ratio threshold.",
                        threshold_label=f"Maximum detour ratio {detour_ratio_threshold:.2f}",
                        observed_label=f"Observed detour ratio {detour_ratio:.2f}",
                    )
                )

        if connection_count <= 1 and total_length > stub_length_threshold:
            risks.append(
                make_risk(
                    rule_id="signal_integrity_advanced",
                    category="signal_integrity",
                    severity="medium",
                    message=f"Critical net {net_name} appears to contain a dangling or stub-like route ({total_length:.2f} units)",
                    recommendation="Remove unused stubs or terminate the route at the intended load to reduce reflection risk.",
                    nets=[net_name],
                    metrics={
                        "trace_length": round(total_length, 2),
                        "threshold": stub_length_threshold,
                        "connection_count": connection_count,
                    },
                    confidence=0.72,
                    short_title="Potential critical stub",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="signal",
                    why_it_matters="Dangling routes and long stubs can reflect energy back into the main signal path.",
                    trigger_condition="Critical-net routed length exceeded the stub threshold while endpoint connectivity stayed unusually low.",
                    threshold_label=f"Maximum stub length {stub_length_threshold:.2f} units",
                    observed_label=f"Observed stub-like length {total_length:.2f} units",
                )
            )

    for index, (left_name, left_net) in enumerate(candidate_nets):
        left_segments = pcb.get_traces_by_net(left_name)
        for right_name, right_net in candidate_nets[index + 1:]:
            if left_name == right_name:
                continue
            right_segments = pcb.get_traces_by_net(right_name)

            for left_segment in left_segments:
                if left_segment.length < crosstalk_parallel_length:
                    continue
                for right_segment in right_segments:
                    if right_segment.length < crosstalk_parallel_length:
                        continue
                    if str(left_segment.layer or "") != str(right_segment.layer or ""):
                        continue

                    similarity = _segment_angle_similarity(left_segment, right_segment)
                    if similarity < crosstalk_parallel_similarity:
                        continue

                    midpoint_distance = _segment_midpoint_distance(left_segment, right_segment)
                    if midpoint_distance > crosstalk_spacing_threshold:
                        continue

                    risks.append(
                        make_risk(
                            rule_id="signal_integrity_advanced",
                            category="signal_integrity",
                            severity="high",
                            message=f"Critical nets {left_name} and {right_name} run closely in parallel on {left_segment.layer}",
                            recommendation="Increase spacing, shorten parallel run length, or adjust layer strategy to reduce crosstalk risk.",
                            nets=[left_name, right_name],
                            metrics={
                                "parallel_similarity": round(similarity, 3),
                                "spacing": round(midpoint_distance, 2),
                                "spacing_threshold": crosstalk_spacing_threshold,
                            },
                            confidence=0.82,
                            short_title="Parallel critical-net crosstalk risk",
                            fix_priority="high",
                            estimated_impact="high",
                            design_domain="signal",
                            why_it_matters="Closely spaced parallel critical traces can capacitively or inductively couple into each other.",
                            trigger_condition="Two critical nets were routed in close parallel alignment on the same layer.",
                            threshold_label=f"Maximum parallel spacing {crosstalk_spacing_threshold:.2f} units",
                            observed_label=f"Observed midpoint spacing {midpoint_distance:.2f} units",
                        )
                    )
                    break
                else:
                    continue
                break

    return risks
