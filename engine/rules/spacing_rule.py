import math
from engine.risk import make_risk


def run_rule(pcb):
    min_distance = 5
    risks = []

    for i in range(len(pcb.components)):
        for j in range(i + 1, len(pcb.components)):
            c1 = pcb.components[i]
            c2 = pcb.components[j]

            distance = math.sqrt((c1.x - c2.x) ** 2 + (c1.y - c2.y) ** 2)

            if distance < min_distance:
                risks.append(
                    make_risk(
                        rule_id="spacing",
                        severity="high",
                        message=f"{c1.ref} and {c2.ref} are too close ({distance:.2f} units)",
                        components=[c1.ref, c2.ref],
                    )
                )

    return risks
