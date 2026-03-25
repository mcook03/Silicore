def run_rule(pcb, config):
    risks = []

    max_length = config.get("max_trace_length", 50)

    for net_name, net in pcb.nets.items():
        if len(net) > max_length:
            risks.append({
                "rule_id": "NET_LENGTH",
                "category": "signal_integrity",
                "severity": "medium",
                "message": f"Net {net_name} is too long ({len(net)} units)",
                "recommendation": "Reduce trace length or improve routing",
                "components": net,
                "nets": [net_name],
                "metrics": {
                    "length": len(net),
                    "threshold": max_length
                }
            })

    return risks