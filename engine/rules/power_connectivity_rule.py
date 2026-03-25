def run_rule(pcb, config):
    risks = []

    power_config = config.get("power", {})
    required_power_nets = power_config.get("required_power_nets", ["VCC", "3V3", "5V", "VIN"])

    normalized_power_nets = [net.upper() for net in required_power_nets]

    active_types = ["IC", "MCU", "REG", "DRIVER", "AMP"]

    for component in getattr(pcb, "components", []):
        component_type = str(getattr(component, "type", "")).upper()
        component_net = getattr(component, "net", None)

        if component_type not in active_types:
            continue

        if not component_net:
            risks.append({
                "rule_id": "power_connectivity",
                "category": "power_integrity",
                "severity": "critical",
                "message": f"{component.ref} has no connected net, so power delivery cannot be verified",
                "recommendation": "Connect the component to the appropriate power rail",
                "components": [component.ref],
                "nets": [],
                "metrics": {
                    "required_power_nets": required_power_nets
                }
            })
            continue

        if str(component_net).upper() not in normalized_power_nets:
            risks.append({
                "rule_id": "power_connectivity",
                "category": "power_integrity",
                "severity": "high",
                "message": f"{component.ref} is on net {component_net}, which is not recognized as a configured power rail",
                "recommendation": "Verify the component power connection or update the configured allowed power nets if this rail is intentional",
                "components": [component.ref],
                "nets": [component_net],
                "metrics": {
                    "required_power_nets": required_power_nets,
                    "detected_net": component_net
                }
            })

    return risks