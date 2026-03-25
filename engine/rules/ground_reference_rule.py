def run_rule(pcb, config):
    risks = []

    emi_config = config.get("emi", {})
    power_config = config.get("power", {})

    require_ground_reference = emi_config.get("require_ground_reference", True)
    ground_nets = power_config.get("required_ground_nets", ["GND", "GROUND"])

    if not require_ground_reference:
        return risks

    for component in getattr(pcb, "components", []):
        component_net = getattr(component, "net", None)
        component_type = str(getattr(component, "type", "")).upper()

        if component_type in ["CAP", "MOUNT", "MECH"]:
            continue

        if not component_net:
            risks.append({
                "rule_id": "ground_reference",
                "category": "emi_return_path",
                "severity": "high",
                "message": f"{component.ref} has no assigned net, so its ground reference cannot be verified",
                "recommendation": "Assign the component to the proper signal or power net and verify its return path to ground",
                "components": [component.ref],
                "nets": [],
                "metrics": {
                    "ground_reference_required": True
                }
            })
            continue

        if str(component_net).upper() in [net.upper() for net in ground_nets]:
            continue

        ground_found = False
        for other in getattr(pcb, "components", []):
            other_net = getattr(other, "net", None)
            if other_net and str(other_net).upper() in [net.upper() for net in ground_nets]:
                ground_found = True
                break

        if not ground_found:
            risks.append({
                "rule_id": "ground_reference",
                "category": "emi_return_path",
                "severity": "critical",
                "message": f"No ground net was found while checking return path context for {component.ref}",
                "recommendation": "Add a valid ground net such as GND and verify signal return paths",
                "components": [component.ref],
                "nets": [component_net],
                "metrics": {
                    "required_ground_nets": ground_nets
                }
            })

    return risks