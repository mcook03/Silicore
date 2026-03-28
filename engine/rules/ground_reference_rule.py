from engine.risk import make_risk


def _normalize_list(values):
    return {
        str(value).strip().upper()
        for value in (values or [])
        if str(value).strip()
    }


def _component_nets(component):
    nets = []

    if hasattr(component, "connected_nets"):
        nets = getattr(component, "connected_nets", []) or []
    elif hasattr(component, "get_nets"):
        try:
            nets = component.get_nets() or []
        except Exception:
            nets = []

    return [
        str(net).strip().upper()
        for net in nets
        if str(net).strip()
    ]


def run_rule(pcb, config):
    risks = []

    emi_config = config.get("emi", {})
    power_config = config.get("power", {})
    rules_config = config.get("rules", {})
    ground_reference_config = rules_config.get("ground_reference", {})

    require_ground_reference = emi_config.get("require_ground_reference", True)
    if not require_ground_reference:
        return risks

    configured_ground_nets = ground_reference_config.get(
        "ground_net_keywords",
        power_config.get("required_ground_nets", ["GND", "GROUND"]),
    )

    ground_keywords = _normalize_list(configured_ground_nets)

    board_nets = {
        str(net_name).strip().upper()
        for net_name in getattr(pcb, "nets", {}).keys()
        if str(net_name).strip()
    }

    board_has_ground = any(
        any(keyword in board_net for keyword in ground_keywords)
        for board_net in board_nets
    )

    # Important:
    # If the board has no ground net at all, let return_path_rule own that failure.
    # Do not create duplicate per-component criticals here.
    if not board_has_ground:
        return risks

    critical_net_keywords = _normalize_list(
        ground_reference_config.get(
            "critical_net_keywords",
            config.get("signal", {}).get("critical_nets", []),
        )
    )

    for component in getattr(pcb, "components", []):
        component_type = str(getattr(component, "type", "")).upper()
        if component_type in ["MOUNT", "MECH", "HOLE"]:
            continue

        nets = _component_nets(component)

        if not nets:
            risks.append(
                make_risk(
                    rule_id="ground_reference",
                    category="emi_return_path",
                    severity="medium",
                    message=f"{component.ref} has no assigned net, so its ground reference cannot be verified",
                    recommendation="Assign the component to the correct signal or power net and verify its reference to ground.",
                    components=[component.ref],
                    nets=[],
                    metrics={
                        "ground_reference_required": True,
                    },
                    confidence=0.75,
                    short_title="Unconnected component",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="emi",
                )
            )
            continue

        has_ground_connection = any(
            any(keyword in net for keyword in ground_keywords)
            for net in nets
        )

        if has_ground_connection:
            continue

        # Only flag if the component touches a critical net and still lacks a visible ground reference.
        touches_critical_net = any(
            any(keyword in net for keyword in critical_net_keywords)
            for net in nets
        )

        if not touches_critical_net:
            continue

        risks.append(
            make_risk(
                rule_id="ground_reference",
                category="emi_return_path",
                severity="medium",
                message=f"{component.ref} is connected to a critical net but no ground reference was identified",
                recommendation="Verify that this component has an appropriate nearby ground reference or return path for the connected critical net.",
                components=[component.ref],
                nets=nets,
                metrics={
                    "critical_net_keywords": sorted(list(critical_net_keywords)),
                    "ground_net_keywords": sorted(list(ground_keywords)),
                },
                confidence=0.7,
                short_title="Weak ground reference",
                fix_priority="medium",
                estimated_impact="moderate",
                design_domain="emi",
            )
        )

    return risks