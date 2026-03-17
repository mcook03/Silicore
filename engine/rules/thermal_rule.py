from math import sqrt

from engine.risk import make_risk

HOT_COMPONENT_KEYWORDS = {
    "regulator",
    "mosfet",
    "transistor",
    "driver",
    "power",
    "buck",
    "boost",
    "q",
    "u",
}


def distance(c1, c2):
    return sqrt((c1.x - c2.x) ** 2 + (c1.y - c2.y) ** 2)


def is_hot_component(component):
    text = f"{component.ref} {component.type} {component.value}".lower()
    return any(keyword in text for keyword in HOT_COMPONENT_KEYWORDS)


def run_rule(pcb, config):
    risks = []
    threshold = config["rules"]["thermal"]["threshold"]

    hot_components = [c for c in pcb.components if is_hot_component(c)]

    for i in range(len(hot_components)):
        for j in range(i + 1, len(hot_components)):
            c1 = hot_components[i]
            c2 = hot_components[j]

            d = distance(c1, c2)

            if d < threshold:
                risks.append(
                    make_risk(
                        rule_id="thermal",
                        category="thermal",
                        severity="high",
                        message=f"{c1.ref} and {c2.ref} may create a thermal hotspot ({d:.2f} units)",
                        recommendation="Increase spacing, improve copper area, or add thermal relief to reduce localized heating.",
                        components=[c1.ref, c2.ref],
                        metrics={
                            "distance": round(d, 2),
                            "threshold": threshold,
                        },
                        confidence=0.8,
                        short_title="Potential thermal hotspot",
                        fix_priority="high",
                        estimated_impact="high",
                        design_domain="thermal",
                    )
                )

    return risks