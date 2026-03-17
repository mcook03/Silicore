from engine.risk import make_risk

POWER_NET_KEYWORDS = {"VCC", "VIN", "VBAT", "5V", "3V3", "12V", "1V8"}


def run_rule(pcb, config):
    risks = []
    min_connections = config["rules"]["power_rail"]["min_connections"]

    for net_name, net in pcb.nets.items():
        upper_name = net_name.upper()

        if not any(keyword in upper_name for keyword in POWER_NET_KEYWORDS):
            continue

        connection_count = len([conn for conn in net.connections if conn[0]])

        if connection_count < min_connections:
            risks.append(
                make_risk(
                    rule_id="power_rail",
                    category="power_integrity",
                    severity="medium",
                    message=f"Power net {net_name} appears weakly connected with only {connection_count} mapped connection(s)",
                    recommendation="Verify the power rail reaches all required loads and that its connectivity is correctly defined.",
                    nets=[net_name],
                    metrics={
                        "connection_count": connection_count,
                        "min_connections": min_connections,
                    },
                    confidence=0.72,
                    short_title="Weak power rail connectivity",
                    fix_priority="high",
                    estimated_impact="high",
                    design_domain="power",
                )
            )

    return risks