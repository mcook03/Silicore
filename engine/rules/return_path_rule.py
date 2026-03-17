from engine.risk import make_risk

GROUND_NET_NAMES = {"GND", "GROUND", "PGND", "AGND"}


def run_rule(pcb, config):
    risks = []

    ground_nets = [name for name in pcb.nets if name.upper() in GROUND_NET_NAMES]
    ground_zone_count = len([zone for zone in pcb.zones if zone.net_name.upper() in GROUND_NET_NAMES])
    min_ground_zones = config["rules"]["return_path"]["min_ground_zones"]

    if not ground_nets:
        risks.append(
            make_risk(
                rule_id="return_path",
                category="signal_integrity",
                severity="high",
                message="No explicit ground net was found, which may indicate poor return path definition",
                recommendation="Ensure the design includes a clear ground reference net and proper return path strategy.",
                metrics={
                    "ground_net_count": 0,
                    "ground_zone_count": ground_zone_count,
                    "min_ground_zones": min_ground_zones,
                },
                confidence=0.88,
                short_title="Missing ground reference",
                fix_priority="high",
                estimated_impact="high",
                design_domain="signal",
            )
        )
        return risks

    if ground_zone_count < min_ground_zones:
        risks.append(
            make_risk(
                rule_id="return_path",
                category="signal_integrity",
                severity="medium",
                message="Ground net exists but no ground zone or copper pour was detected for return path support",
                recommendation="Consider adding a continuous ground plane or ground pour to improve return current paths.",
                nets=ground_nets,
                metrics={
                    "ground_net_count": len(ground_nets),
                    "ground_zone_count": ground_zone_count,
                    "min_ground_zones": min_ground_zones,
                },
                confidence=0.76,
                short_title="Weak return path support",
                fix_priority="high",
                estimated_impact="high",
                design_domain="signal",
            )
        )

    return risks