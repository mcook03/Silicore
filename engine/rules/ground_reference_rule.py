def run_rule(pcb, config):
    risks = []

    ground_nets = ["GND", "GROUND"]

    for component in pcb.components:
        if not component.net:
            risks.append({
                "rule_id": "GROUND_REFERENCE",
                "category": "emi_return_path",
                "severity": "high",
                "message": f"{component.ref} has no ground reference",
                "recommendation": "Ensure component is connected to a valid ground net",
                "components": [component.ref],
                "nets": [],
                "metrics": {}
            })
        elif component.net not in ground_nets:
            # optional mild warning if needed later
            pass

    return risks