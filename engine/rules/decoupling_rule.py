from math import sqrt

from engine.risk import make_risk

TARGET_TYPES = {"atmega328", "mcu", "microcontroller", "ic", "processor", "controller"}


def distance(c1, c2):
    return sqrt((c1.x - c2.x) ** 2 + (c1.y - c2.y) ** 2)


def is_target_component(component):
    text = f"{component.type} {component.value}".lower()
    return any(keyword in text for keyword in TARGET_TYPES)


def is_capacitor(component):
    text = f"{component.type} {component.value} {component.ref}".lower()
    return "cap" in text or component.ref.upper().startswith("C")


def run_rule(pcb, config):
    risks = []
    threshold = config["rules"]["decoupling"]["threshold"]

    for comp in pcb.components:
        if not is_target_component(comp):
            continue

        nearest_cap_distance = None

        for other in pcb.components:
            if comp.ref == other.ref:
                continue

            if not is_capacitor(other):
                continue

            d = distance(comp, other)

            if nearest_cap_distance is None or d < nearest_cap_distance:
                nearest_cap_distance = d

        if nearest_cap_distance is None or nearest_cap_distance > threshold:
            risks.append(
                make_risk(
                    rule_id="decoupling",
                    category="power_integrity",
                    severity="medium",
                    message=f"{comp.ref} ({comp.value}) has no nearby decoupling capacitor",
                    recommendation="Place a 100nF decoupling capacitor close to the device power pin.",
                    components=[comp.ref],
                    metrics={
                        "nearest_cap_distance": round(nearest_cap_distance, 2) if nearest_cap_distance is not None else None,
                        "threshold": threshold,
                    },
                    confidence=0.85,
                    short_title="Missing nearby decoupling",
                    fix_priority="high",
                    estimated_impact="high",
                    design_domain="power",
                )
            )

    return risks