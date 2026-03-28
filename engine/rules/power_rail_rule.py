from engine.risk import make_risk


def is_power_net(net_name, keywords):
    upper_name = str(net_name).upper()
    return any(keyword.upper() in upper_name for keyword in keywords)


def run_rule(pcb, config):
    risks = []
    rule_config = config.get("rules", {}).get("power_rail", {})

    min_connections = int(rule_config.get("min_connections", 2))
    max_trace_length = float(rule_config.get("max_trace_length", 50.0))
    min_trace_width = float(rule_config.get("min_trace_width", 0.5))
    max_via_count = int(rule_config.get("max_via_count", 5))
    power_net_keywords = rule_config.get(
        "power_net_keywords",
        ["VCC", "VIN", "VBAT", "5V", "3V3", "VDD"]
    )

    for net_name, net in getattr(pcb, "nets", {}).items():
        if not is_power_net(net_name, power_net_keywords):
            continue

        connection_count = len(getattr(net, "connections", []))
        total_length = getattr(net, "total_trace_length", 0.0)
        min_width = getattr(net, "min_trace_width", None)
        via_count = getattr(net, "via_count", 0)

        if connection_count < min_connections:
            risks.append(
                make_risk(
                    rule_id="power_rail",
                    category="power_integrity",
                    severity="medium",
                    message=f"Power net {net_name} has too few connections ({connection_count})",
                    recommendation="Check whether the power net is properly distributed to all intended loads.",
                    nets=[net_name],
                    metrics={
                        "connections": connection_count,
                        "minimum_expected": min_connections,
                    },
                )
            )

        if total_length > max_trace_length:
            risks.append(
                make_risk(
                    rule_id="power_rail",
                    category="power_integrity",
                    severity="high",
                    message=f"Power net {net_name} has excessive routed length ({total_length:.2f} units)",
                    recommendation="Reduce power path length or improve distribution topology to lower impedance and voltage drop risk.",
                    nets=[net_name],
                    metrics={
                        "trace_length": round(total_length, 2),
                        "threshold": max_trace_length,
                    },
                )
            )

        if min_width is not None and min_width < min_trace_width:
            risks.append(
                make_risk(
                    rule_id="power_rail",
                    category="power_integrity",
                    severity="high",
                    message=f"Power net {net_name} uses a narrow trace width ({min_width:.2f})",
                    recommendation="Increase power trace width to reduce resistance, heating, and voltage drop.",
                    nets=[net_name],
                    metrics={
                        "trace_width": min_width,
                        "minimum_expected": min_trace_width,
                    },
                )
            )

        if via_count > max_via_count:
            risks.append(
                make_risk(
                    rule_id="power_rail",
                    category="power_integrity",
                    severity="medium",
                    message=f"Power net {net_name} uses many vias ({via_count}) which may increase impedance",
                    recommendation="Reduce unnecessary via transitions on critical power nets where possible.",
                    nets=[net_name],
                    metrics={
                        "via_count": via_count,
                        "threshold": max_via_count,
                    },
                )
            )

    return risks