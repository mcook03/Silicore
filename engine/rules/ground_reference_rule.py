def run_rule(pcb, config):
    risks = []

    ground_keywords = config["rules"]["ground_reference"]["ground_net_keywords"]

    for component in pcb.components:
        nets = []

        if hasattr(component, "get_nets"):
            nets = component.get_nets()

        if not nets:
            risks.append({
                "rule_id": "ground_reference",
                "category": "emi_return_path",
                "severity": "medium",
                "message": f"{component.ref} has no assigned net, so its ground reference cannot be verified",
                "recommendation": "Assign the component to the proper signal or power net and verify its return path to ground.",
                "components": [component.ref]
            })
            continue

        has_ground = any(
            any(gnd in net.upper() for gnd in ground_keywords)
            for net in nets
        )

        if not has_ground:
            risks.append({
                "rule_id": "ground_reference",
                "category": "emi_return_path",
                "severity": "medium",
                "message": f"{component.ref} has no ground reference",
                "recommendation": "Ensure this component has a return path to ground.",
                "components": [component.ref],
                "nets": nets
            })

    return risks