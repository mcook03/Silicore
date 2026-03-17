from math import sqrt

from engine.risk import make_risk

REGULATOR_KEYWORDS = {"regulator", "buck", "boost", "ldo", "pmic", "power"}
LOAD_KEYWORDS = {"mcu", "microcontroller", "processor", "fpga", "driver", "sensor", "ic"}


def distance(c1, c2):
    return sqrt((c1.x - c2.x) ** 2 + (c1.y - c2.y) ** 2)


def is_regulator(component):
    text = f"{component.ref} {component.type} {component.value}".lower()
    return any(keyword in text for keyword in REGULATOR_KEYWORDS) or component.ref.upper().startswith("U")


def is_load(component):
    text = f"{component.ref} {component.type} {component.value}".lower()
    return any(keyword in text for keyword in LOAD_KEYWORDS) or component.ref.upper().startswith("U")


def run_rule(pcb, config):
    risks = []
    threshold = config["rules"]["power_distribution"]["threshold"]

    regulators = [c for c in pcb.components if is_regulator(c)]
    loads = [c for c in pcb.components if is_load(c)]

    if not regulators or not loads:
        return risks

    for load in loads:
        nearest_reg = None
        nearest_distance = None

        for reg in regulators:
            if reg.ref == load.ref:
                continue

            d = distance(load, reg)

            if nearest_distance is None or d < nearest_distance:
                nearest_distance = d
                nearest_reg = reg

        if nearest_reg is not None and nearest_distance is not None and nearest_distance > threshold:
            risks.append(
                make_risk(
                    rule_id="power_distribution",
                    category="power_integrity",
                    severity="high",
                    message=f"{load.ref} may have poor power delivery because nearest regulator {nearest_reg.ref} is {nearest_distance:.2f} units away",
                    recommendation="Move the regulator closer to the load or improve the power delivery path with lower-impedance routing.",
                    components=[load.ref, nearest_reg.ref],
                    metrics={
                        "distance": round(nearest_distance, 2),
                        "threshold": threshold,
                    },
                    confidence=0.78,
                    short_title="Weak power distribution path",
                    fix_priority="high",
                    estimated_impact="high",
                    design_domain="power",
                )
            )

    return risks