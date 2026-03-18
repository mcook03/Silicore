from math import sqrt

from engine.risk import make_risk


def distance(c1, c2):
    return sqrt((c1.x - c2.x) ** 2 + (c1.y - c2.y) ** 2)


def is_hot_component(component, hot_keywords):
    text = f"{component.ref} {component.type} {component.value}".lower()
    return any(keyword.lower() in text for keyword in hot_keywords)


def run_rule(pcb, config):
    risks = []
    rule_config = config["rules"]["thermal"]

    threshold = rule_config["threshold"]
    hot_keywords = rule_config["hot_keywords"]

    hot_components = [c for c in pcb.components if is_hot_component(c, hot_keywords)]

    for i in range(len(hot_components)):
        for j in range(i + 1, len(hot_components)):
            c1 = hot_components[i]
            c2 = hot_components[j]

            if c1.layer and c2.layer and c1.layer != c2.layer:
                continue

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
                            "same_layer": c1.layer == c2.layer,
                        },
                        confidence=0.85,
                        short_title="Potential thermal hotspot",
                        fix_priority="high",
                        estimated_impact="high",
                        design_domain="thermal",
                    )
                )

    return risks