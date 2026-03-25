def run_rule(pcb, config):
    risks = []

    power_nets = ["VCC", "3V3", "5V", "VIN"]

    for component in pcb.components:
        if component.type in ["IC", "MCU"]:
            if not component.net or component.net not in power_nets:
                risks.append({
                    "rule_id": "POWER_CONNECTIVITY",
                    "category": "power_integrity",
                    "severity": "critical",
                    "message": f"{component.ref} may not be properly powered",
                    "recommendation": "Connect to correct power rail",
                    "components": [component.ref],
                    "nets": [component.net] if component.net else [],
                    "metrics": {}
                })

    return risks