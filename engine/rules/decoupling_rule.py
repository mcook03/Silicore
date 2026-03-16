import math
from engine.risk import make_risk


def run_rule(pcb):
    max_distance = 6
    risks = []

    mcus = [c for c in pcb.components if c.type.strip().upper() == "MCU"]
    capacitors = [c for c in pcb.components if c.type.strip().upper() == "CAPACITOR"]

    for mcu in mcus:
        has_nearby_cap = False

        for cap in capacitors:
            distance = math.sqrt((mcu.x - cap.x) ** 2 + (mcu.y - cap.y) ** 2)
            if distance <= max_distance:
                has_nearby_cap = True
                break

        if not has_nearby_cap:
            risks.append(
                make_risk(
                    rule_id="decoupling",
                    category="power_integrity",
                    severity="medium",
                    message=f"{mcu.ref} ({mcu.value}) has no nearby decoupling capacitor",
                    recommendation="Place a 100nF decoupling capacitor close to the MCU power pin.",
                    components=[mcu.ref],
                )
            )

    return risks