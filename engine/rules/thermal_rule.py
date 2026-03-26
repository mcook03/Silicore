from math import sqrt
from engine.risk import make_risk


def distance(c1, c2):
    return sqrt((c1.x - c2.x) ** 2 + (c1.y - c2.y) ** 2)


def is_hot_component(component, keywords):
    text = f"{component.ref} {component.type} {component.value}".lower()
    return any(keyword.lower() in text for keyword in keywords)


def run_rule(pcb, config):
    risks = []
    rule_config = config.get("rules", {}).get("thermal", {})
    thermal_config = config.get("thermal", {})

    threshold = float(
        rule_config.get(
            "threshold",
            thermal_config.get("hotspot_distance_threshold", 4.0),
        )
    )

    hot_keywords = rule_config.get(
        "hot_component_keywords",
        ["U", "Q", "VRM", "REG", "LDO", "BUCK", "BOOST", "MOSFET", "DRV", "AMP", "CPU", "FPGA", "POWER"],
    )

    hot_components = [c for c in pcb.components if is_hot_component(c, hot_keywords)]

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
                        severity="medium",
                        message=f"{c1.ref} and {c2.ref} may create a thermal hotspot ({d:.2f} units apart)",
                        recommendation="Increase spacing, improve copper spreading, or review local thermal management around these components.",
                        components=[c1.ref, c2.ref],
                        metrics={
                            "distance": round(d, 2),
                            "threshold": threshold,
                        },
                        confidence=0.8,
                        short_title="Possible thermal hotspot",
                        fix_priority="medium",
                        estimated_impact="moderate",
                        design_domain="thermal",
                    )
                )

    return risks