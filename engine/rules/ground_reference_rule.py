from engine.risk import make_risk


def run_rule(pcb, config):
    risks = []

    emi_config = config.get("emi", {})
    power_config = config.get("power", {})

    require_ground_reference = emi_config.get("require_ground_reference", True)
    if not require_ground_reference:
        return risks

    ground_nets = {
        str(net).strip().upper()
        for net in power_config.get("required_ground_nets", ["GND", "GROUND"])
        if str(net).strip()
    }

    components = getattr(pcb, "components", [])
    board_nets = {
        str(net_name).strip().upper()
        for net_name in getattr(pcb, "nets", {}).keys()
        if str(net_name).strip()
    }

    ground_exists = any(net in ground_nets for net in board_nets)

    for component in components:
        component_type = str(getattr(component, "type", "")).upper()

        if component_type in ["MOUNT", "MECH"]:
            continue

        nets = [
            str(net).strip().upper()
            for net in getattr(component, "connected_nets", []) or []
            if str(net).strip()
        ]

        if not nets:
            risks.append(
                make_risk(
                    rule_id="ground_reference",
                    category="emi_return_path",
                    severity="medium",
                    message=f"{component.ref} has no assigned net, so its ground reference cannot be verified",
                    recommendation="Assign the component to the proper signal or power net and verify its return path to ground.",
                    components=[component.ref],
                    nets=[],
                    metrics={
                        "ground_reference_required": True
                    },
                    confidence=0.75,
                    short_title="Unconnected component",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="emi",
                )
            )
            continue

        if any(net in ground_nets for net in nets):
            continue

        if not ground_exists:
            risks.append(
                make_risk(
                    rule_id="ground_reference",
                    category="emi_return_path",
                    severity="critical",
                    message=f"No ground net was found while checking reference context for {component.ref}",
                    recommendation="Add a valid ground net such as GND and verify signal return paths.",
                    components=[component.ref],
                    nets=nets,
                    metrics={
                        "required_ground_nets": sorted(list(ground_nets))
                    },
                    confidence=0.9,
                    short_title="Missing board ground",
                    fix_priority="high",
                    estimated_impact="high",
                    design_domain="emi",
                )
            )

    return risks