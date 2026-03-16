import math
from engine.risk import make_risk


def run_rule(pcb):
    max_distance = 15
    risks = []

    regulators = [c for c in pcb.components if c.type.strip().upper() == "REGULATOR"]
    mcus = [c for c in pcb.components if c.type.strip().upper() == "MCU"]

    for mcu in mcus:
        closest_distance = None
        closest_reg = None

        for reg in regulators:
            dx = mcu.x - reg.x
            dy = mcu.y - reg.y
            distance = math.sqrt(dx ** 2 + dy ** 2)

            if closest_distance is None or distance < closest_distance:
                closest_distance = distance
                closest_reg = reg

        if closest_distance is None or closest_distance > max_distance:
            if closest_reg is not None:
                risks.append(
                    make_risk(
                        rule_id="power_distribution",
                        severity="high",
                        message=f"{mcu.ref} may have poor power delivery because nearest regulator {closest_reg.ref} is {closest_distance:.2f} units away",
                        components=[mcu.ref, closest_reg.ref],
                    )
                )
            else:
                risks.append(
                    make_risk(
                        rule_id="power_distribution",
                        severity="critical",
                        message=f"{mcu.ref} may have poor power delivery because no regulator was found",
                        components=[mcu.ref],
                    )
                )

    return risks