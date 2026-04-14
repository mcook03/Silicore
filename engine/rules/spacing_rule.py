from math import sqrt
from engine.risk import make_risk


def distance(c1, c2):
    return sqrt((c1.x - c2.x) ** 2 + (c1.y - c2.y) ** 2)


def run_rule(pcb, config):
    risks = []
    rule_config = config.get("rules", {}).get("spacing", {})
    layout_config = config.get("layout", {})

    threshold = float(
        rule_config.get(
            "threshold",
            layout_config.get("min_component_spacing", 3.0),
        )
    )

    components = getattr(pcb, "components", [])

    for i in range(len(components)):
        for j in range(i + 1, len(components)):
            c1 = components[i]
            c2 = components[j]
            d = distance(c1, c2)

            if d < threshold:
                risks.append(
                    make_risk(
                        rule_id="spacing",
                        category="layout",
                        severity="high",
                        message=f"{c1.ref} and {c2.ref} are too close ({d:.2f} units)",
                        recommendation="Increase spacing between these components to improve manufacturability and routing clearance.",
                        components=[c1.ref, c2.ref],
                        metrics={
                            "distance": round(d, 2),
                            "threshold": threshold,
                        },
                        confidence=0.95,
                        short_title="Insufficient component spacing",
                        fix_priority="high",
                        estimated_impact="moderate",
                        design_domain="layout",
                        trigger_condition="Component pair spacing fell below the configured minimum spacing threshold.",
                        threshold_label=f"Minimum spacing {threshold:.2f} units",
                        observed_label=f"Observed spacing {d:.2f} units",
                    )
                )

    return risks
