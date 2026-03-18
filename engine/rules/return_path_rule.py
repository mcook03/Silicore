from engine.risk import make_risk

GROUND_NET_NAMES = {"GND", "GROUND", "PGND", "AGND"}


def run_rule(pcb, config):
    risks = []
    rule_config = config["rules"]["return_path"]

    min_ground_zones = rule_config["min_ground_zones"]
    require_ground_net = rule_config["require_ground_net"]

    ground_nets = [name for name in pcb.nets if name.upper() in GROUND_NET_NAMES]
    ground_zone_count = len([zone for zone in pcb.zones if zone.net_name.upper() in GROUND_NET_NAMES])

    if require_ground_net and not ground_nets:
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

    if ground_nets and ground_zone_count < min_ground_zones:
        risks.append(
            make_risk(
                rule_id="return_path",
                category="signal_integrity",
                severity="medium",
                message="Ground net exists but ground-zone support appears insufficient for robust return paths",
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

    signal_nets = []
    for net_name in pcb.nets:
        upper = net_name.upper()
        if upper not in GROUND_NET_NAMES and upper not in {"VCC", "VIN", "VBAT", "3V3", "5V", "12V"}:
            signal_nets.append(net_name)

    if signal_nets and ground_zone_count == 0:
        risks.append(
            make_risk(
                rule_id="return_path",
                category="signal_integrity",
                severity="medium",
                message=f"{len(signal_nets)} signal net(s) exist without any detected ground-zone support",
                recommendation="Add or verify ground pours/planes near signal routing to improve return current continuity.",
                nets=signal_nets[:10],
                metrics={
                    "signal_net_count": len(signal_nets),
                    "ground_zone_count": ground_zone_count,
                },
                confidence=0.74,
                short_title="Signals lack return-path support",
                fix_priority="high",
                estimated_impact="high",
                design_domain="signal",
            )
        )

    return risks