import math
from engine.risk import make_risk


def run_rule(pcb):
    max_distance = 8
    risks = []

    heat_types = {"REGULATOR", "MOSFET", "POWER", "DRIVER"}
    heat_components = [
        c for c in pcb.components if c.type.strip().upper() in heat_types
    ]

    for i in range(len(heat_components)):
        for j in range(i + 1, len(heat_components)):
            c1 = heat_components[i]
            c2 = heat_components[j]

            distance = math.sqrt((c1.x - c2.x) ** 2 + (c1.y - c2.y) ** 2)

            if distance <= max_distance:
                risks.append(
                    make_risk(
                        rule_id="thermal",
                        severity="high",
                        message=f"{c1.ref} and {c2.ref} may create a thermal hotspot ({distance:.2f} units)",
                        components=[c1.ref, c2.ref],
                    )
                )

    return risks