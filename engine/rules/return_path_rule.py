from engine.risk import make_risk


def _upper_set(values):
    return {str(value).strip().upper() for value in values if str(value).strip()}


def run_rule(pcb, config):
    risks = []

    emi_config = config.get("emi", {})
    power_config = config.get("power", {})
    signal_config = config.get("signal", {})
    rule_config = config.get("rules", {}).get("return_path", {})

    require_ground_reference = rule_config.get(
        "require_ground_reference",
        emi_config.get("require_ground_reference", True)
    )
    if not require_ground_reference:
        return risks

    ground_nets = _upper_set(
        rule_config.get(
            "ground_nets",
            power_config.get("required_ground_nets", ["GND", "GROUND"])
        )
    )

    critical_nets = _upper_set(
        rule_config.get(
            "critical_nets",
            signal_config.get("critical_nets", ["CLK", "SCL", "SDA", "MOSI", "MISO", "CS"])
        )
    )

    board_nets = set()
    for net_name in getattr(pcb, "nets", {}).keys():
        clean_name = str(net_name).strip().upper()
        if clean_name:
            board_nets.add(clean_name)

    ground_present = any(net in ground_nets for net in board_nets)

    if not ground_present:
        signal_components = []

        for component in getattr(pcb, "components", []):
            component_type = str(getattr(component, "type", "")).upper()
            if component_type in ["CAP", "MOUNT", "MECH"]:
                continue

            component_nets = [
                str(net).strip().upper()
                for net in getattr(component, "connected_nets", []) or []
                if str(net).strip()
            ]

            if component_nets:
                signal_components.append(component.ref)

        if signal_components:
            risks.append(
                make_risk(
                    rule_id="return_path",
                    category="emi_return_path",
                    severity="critical",
                    message="No valid ground net was found on the board, so return-path continuity cannot be verified",
                    recommendation="Add a valid ground net such as GND and ensure critical signals have a continuous return path.",
                    components=signal_components,
                    nets=sorted(list(board_nets)),
                    metrics={
                        "ground_present": ground_present,
                        "required_ground_nets": sorted(list(ground_nets)),
                        "board_nets": sorted(list(board_nets)),
                    },
                    confidence=0.92,
                    short_title="Missing board ground reference",
                    fix_priority="high",
                    estimated_impact="high",
                    design_domain="emi",
                )
            )

        return risks

    for component in getattr(pcb, "components", []):
        component_type = str(getattr(component, "type", "")).upper()

        if component_type in ["CAP", "MOUNT", "MECH"]:
            continue

        component_nets = [
            str(net).strip().upper()
            for net in getattr(component, "connected_nets", []) or []
            if str(net).strip()
        ]

        if not component_nets:
            continue

        component_critical_nets = [net for net in component_nets if net in critical_nets]

        if not component_critical_nets:
            continue

        if any(net in ground_nets for net in component_nets):
            continue

        risks.append(
            make_risk(
                rule_id="return_path",
                category="emi_return_path",
                severity="high",
                message=(
                    f"{component.ref} is connected to critical net(s) "
                    f"{', '.join(component_critical_nets)} but has no direct ground-reference net"
                ),
                recommendation="Review this signal path and ensure it has a nearby continuous ground reference and a clean return path.",
                components=[component.ref],
                nets=component_critical_nets,
                metrics={
                    "critical_nets": component_critical_nets,
                    "required_ground_nets": sorted(list(ground_nets)),
                    "ground_present": ground_present,
                },
                confidence=0.82,
                short_title="Weak return-path reference",
                fix_priority="high",
                estimated_impact="high",
                design_domain="emi",
            )
        )

    return risks