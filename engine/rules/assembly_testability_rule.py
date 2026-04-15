from math import sqrt

from engine.risk import make_risk


def _distance(x1, y1, x2, y2):
    return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def _upper_list(values):
    return [str(value).strip().upper() for value in (values or []) if str(value).strip()]


def _is_testpoint(component):
    text = f"{getattr(component, 'ref', '')} {getattr(component, 'value', '')} {getattr(component, 'type', '')}".upper()
    return text.startswith("TP") or "TEST" in text


def _is_fiducial(component):
    text = f"{getattr(component, 'ref', '')} {getattr(component, 'value', '')} {getattr(component, 'type', '')}".upper()
    return text.startswith("FID") or "FIDUCIAL" in text


def _matches(net_name, keywords):
    upper = str(net_name or "").strip().upper()
    return any(keyword in upper for keyword in keywords)


def run_rule(pcb, config):
    risks = []
    rule_config = config.get("rules", {}).get("assembly_testability", {})
    signal_config = config.get("signal", {})
    power_config = config.get("power", {})

    min_fiducials = int(rule_config.get("min_fiducials", 2))
    probe_access_radius = float(rule_config.get("probe_access_radius", 6.0))
    min_ground_test_points = int(rule_config.get("min_ground_test_points", 1))

    critical_keywords = _upper_list(signal_config.get("critical_nets", []) + ["RESET", "SWD", "JTAG", "UART", "USB", "BOOT"])
    ground_keywords = _upper_list(power_config.get("required_ground_nets", ["GND", "GROUND"]))

    testpoints = [component for component in getattr(pcb, "components", []) if _is_testpoint(component)]
    fiducials = [component for component in getattr(pcb, "components", []) if _is_fiducial(component)]

    if len(fiducials) < min_fiducials:
        risks.append(
            make_risk(
                rule_id="assembly_testability",
                category="assembly_testability",
                severity="medium",
                message="Board has limited visible fiducial strategy for assembly alignment",
                recommendation="Add global fiducials to improve assembly registration and inspection consistency.",
                components=[component.ref for component in fiducials[:4]],
                metrics={
                    "fiducials": len(fiducials),
                    "threshold": min_fiducials,
                },
                confidence=0.76,
                short_title="Weak fiducial coverage",
                fix_priority="medium",
                estimated_impact="moderate",
                design_domain="manufacturing",
                why_it_matters="Consistent fiducial strategy helps automated assembly and optical alignment stay reliable.",
                trigger_condition="Visible fiducial count fell below the configured assembly threshold.",
                threshold_label=f"Minimum fiducials {min_fiducials}",
                observed_label=f"Observed fiducials {len(fiducials)}",
            )
        )

    ground_test_points = 0
    testpoint_nets = set()
    for component in testpoints:
        for pad in getattr(component, "pads", []):
            net_name = str(getattr(pad, "net_name", "")).strip().upper()
            if not net_name:
                continue
            testpoint_nets.add(net_name)
            if _matches(net_name, ground_keywords):
                ground_test_points += 1

    if ground_test_points < min_ground_test_points:
        risks.append(
            make_risk(
                rule_id="assembly_testability",
                category="assembly_testability",
                severity="medium",
                message="Ground test-point coverage appears limited for bring-up and probing",
                recommendation="Add at least one accessible ground test point so probing and scope reference setup are easier during bring-up.",
                components=[component.ref for component in testpoints[:4]],
                metrics={
                    "ground_test_points": ground_test_points,
                    "threshold": min_ground_test_points,
                },
                confidence=0.81,
                short_title="Limited ground test access",
                fix_priority="medium",
                estimated_impact="moderate",
                design_domain="testability",
                why_it_matters="Ground test points are foundational for repeatable probing, debug, and validation.",
                trigger_condition="Visible ground test-point count fell below the configured minimum.",
                threshold_label=f"Minimum ground test points {min_ground_test_points}",
                observed_label=f"Observed ground test points {ground_test_points}",
            )
        )

    for net_name, net in getattr(pcb, "nets", {}).items():
        upper_net = str(net_name).strip().upper()
        if not _matches(upper_net, critical_keywords):
            continue
        if upper_net in testpoint_nets:
            continue
        risks.append(
            make_risk(
                rule_id="assembly_testability",
                category="assembly_testability",
                severity="medium",
                message=f"Critical or debug-oriented net {upper_net} has no visible test point",
                recommendation="Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.",
                components=[component_ref for component_ref, _ in getattr(net, "connections", [])[:4]],
                nets=[upper_net],
                metrics={
                    "has_testpoint": False,
                },
                confidence=0.72,
                short_title="Missing critical-net test access",
                fix_priority="medium",
                estimated_impact="moderate",
                design_domain="testability",
                why_it_matters="Critical nets that cannot be probed easily make validation, factory test, and field debug slower and more expensive.",
                trigger_condition="A critical or debug-oriented net was identified without any visible test-point component.",
                threshold_label="Expected at least one visible access point on critical nets",
                observed_label="Observed visible access point: none",
            )
        )

    header_like = []
    for component in getattr(pcb, "components", []):
        text = f"{getattr(component, 'ref', '')} {getattr(component, 'value', '')} {getattr(component, 'type', '')}".upper()
        if text.startswith("J") or "HEADER" in text or "DEBUG" in text or "PROG" in text:
            header_like.append(component)

    for component in header_like:
        blockers = 0
        nearby = []
        for other in getattr(pcb, "components", []):
            if other.ref == component.ref:
                continue
            distance = _distance(component.x, component.y, other.x, other.y)
            if distance < probe_access_radius:
                blockers += 1
                nearby.append(other.ref)
        if blockers >= 4:
            risks.append(
                make_risk(
                    rule_id="assembly_testability",
                    category="assembly_testability",
                    severity="low",
                    message=f"Header or debug access point {component.ref} is crowded by nearby components",
                    recommendation="Open more clearance around the debug or programming entry point to make probing and rework easier.",
                    components=[component.ref] + nearby[:4],
                    metrics={
                        "nearby_components": blockers,
                        "probe_access_radius": probe_access_radius,
                    },
                    confidence=0.68,
                    short_title="Crowded debug access region",
                    fix_priority="low",
                    estimated_impact="moderate",
                    design_domain="testability",
                    why_it_matters="Connectors and debug headers that are boxed in by nearby parts are harder to use during bring-up or service.",
                    trigger_condition="A header-like component had multiple nearby neighbors inside the configured probe-access radius.",
                    threshold_label=f"Probe-access radius {probe_access_radius:.2f} units",
                    observed_label=f"Observed nearby blockers {blockers}",
                )
            )

    return risks
