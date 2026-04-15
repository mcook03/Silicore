from engine.risk import make_risk


def _normalize(values):
    return {str(value).strip().upper() for value in (values or []) if str(value).strip()}


def run_rule(pcb, config):
    risks = []
    rule_config = config.get("rules", {}).get("reliability", {})
    power_config = config.get("power", {})

    ground_keywords = _normalize(
        rule_config.get(
            "ground_keywords",
            power_config.get("required_ground_nets", ["GND", "GROUND"]),
        )
    )
    min_ground_vias = int(rule_config.get("min_ground_vias", 2))
    min_ground_connections = int(rule_config.get("min_ground_connections", 4))

    board_layers = len(getattr(pcb, "layers", set()) or set())

    for net_name, net in getattr(pcb, "nets", {}).items():
        upper_net = str(net_name).strip().upper()
        if upper_net not in ground_keywords:
            continue

        via_count = len(getattr(net, "vias", []) or [])
        connection_count = len(getattr(net, "connections", []) or [])

        if board_layers > 1 and via_count < min_ground_vias:
            risks.append(
                make_risk(
                    rule_id="reliability",
                    category="reliability",
                    severity="medium",
                    message=f"Ground strategy looks light on stitching support for net {upper_net} ({via_count} vias)",
                    recommendation="Add more stitching or reference vias to strengthen grounding continuity and return-current robustness.",
                    nets=[upper_net],
                    metrics={
                        "ground_via_count": via_count,
                        "threshold": min_ground_vias,
                        "board_layers": board_layers,
                    },
                    confidence=0.82,
                    short_title="Sparse ground stitching",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="reliability",
                    why_it_matters="Weak ground stitching can reduce return-path quality and board robustness outside ideal lab conditions.",
                    trigger_condition="Ground via count fell below the configured minimum stitching threshold for a multi-layer board.",
                    threshold_label=f"Minimum ground vias {min_ground_vias}",
                    observed_label=f"Observed ground vias {via_count}",
                )
            )

        if connection_count < min_ground_connections:
            risks.append(
                make_risk(
                    rule_id="reliability",
                    category="reliability",
                    severity="medium",
                    message=f"Ground net {upper_net} has limited visible connectivity ({connection_count} connections)",
                    recommendation="Review grounding strategy and ensure intended loads and returns are visibly tied into the board ground structure.",
                    nets=[upper_net],
                    metrics={
                        "ground_connections": connection_count,
                        "threshold": min_ground_connections,
                    },
                    confidence=0.74,
                    short_title="Weak visible ground coverage",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="reliability",
                    why_it_matters="Insufficient ground connectivity can increase susceptibility to EMI, transient issues, and inconsistent field behavior.",
                    trigger_condition="Ground connectivity count fell below the configured reliability threshold.",
                    threshold_label=f"Minimum ground connections {min_ground_connections}",
                    observed_label=f"Observed ground connections {connection_count}",
                )
            )

    return risks
