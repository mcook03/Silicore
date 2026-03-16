import math
from engine.risk import make_risk


def run_rule(pcb):
    max_signal_length = 40
    risks = []

    for net_name, net in pcb.nets.items():
        if net_name in {"GND", "VIN", "VOUT"}:
            continue

        if len(net.connections) < 2:
            continue

        for i in range(len(net.connections)):
            for j in range(i + 1, len(net.connections)):
                ref1, _ = net.connections[i]
                ref2, _ = net.connections[j]

                c1 = pcb.get_component(ref1)
                c2 = pcb.get_component(ref2)

                if c1 and c2:
                    distance = math.sqrt((c1.x - c2.x) ** 2 + (c1.y - c2.y) ** 2)

                    if distance > max_signal_length:
                        risks.append(
                            make_risk(
                                rule_id="signal_path",
                                category="signal_integrity",
                                severity="medium",
                                message=f"Net {net_name} has a long signal path between {ref1} and {ref2} ({distance:.2f} units)",
                                recommendation="Reduce path length or improve routing to lower noise and signal quality risks.",
                                components=[ref1, ref2],
                                nets=[net_name],
                            )
                        )

    return risks