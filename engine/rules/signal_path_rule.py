from math import sqrt

from engine.risk import make_risk

EXCLUDED_NETS = {"GND", "GROUND", "VCC", "VIN", "VBAT", "3V3", "5V", "12V"}


def distance(c1, c2):
    return sqrt((c1.x - c2.x) ** 2 + (c1.y - c2.y) ** 2)


def run_rule(pcb, config):
    risks = []
    threshold = config["rules"]["signal_path"]["threshold"]

    for net_name, net in pcb.nets.items():
        if net_name.upper() in EXCLUDED_NETS:
            continue

        valid_connections = [conn for conn in net.connections if conn[0]]
        if len(valid_connections) < 2:
            continue

        for i in range(len(valid_connections)):
            for j in range(i + 1, len(valid_connections)):
                ref1, _ = valid_connections[i]
                ref2, _ = valid_connections[j]

                c1 = pcb.get_component(ref1)
                c2 = pcb.get_component(ref2)

                if c1 is None or c2 is None:
                    continue

                d = distance(c1, c2)

                if d > threshold:
                    risks.append(
                        make_risk(
                            rule_id="signal_path",
                            category="signal_integrity",
                            severity="medium",
                            message=f"Net {net_name} has a long signal path between {c1.ref} and {c2.ref} ({d:.2f} units)",
                            recommendation="Reduce path length or improve routing to lower noise and signal quality risks.",
                            components=[c1.ref, c2.ref],
                            nets=[net_name],
                            metrics={
                                "distance": round(d, 2),
                                "threshold": threshold,
                            },
                            confidence=0.82,
                            short_title="Long signal path",
                            fix_priority="medium",
                            estimated_impact="moderate",
                            design_domain="signal",
                        )
                    )

    return risks