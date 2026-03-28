def run_rule(pcb, config):
    risks = []

    power_nets = config["rules"]["power_connectivity"]["required_power_nets"]

    for component in pcb.components:
        nets = []

        if hasattr(component, "get_nets"):
            nets = component.get_nets()

        if not nets:
            continue

        for net in nets:
            if not any(pwr in net.upper() for pwr in power_nets):
                continue

            # valid power net found
            break
        else:
            risks.append({
                "rule_id": "power_connectivity",
                "category": "power_integrity",
                "severity": "high",
                "message": f"{component.ref} is not connected to a valid power rail",
                "recommendation": "Connect the component to a valid power rail.",
                "components": [component.ref],
                "nets": nets
            })

    return risks