from math import sqrt
from engine.risk import make_risk


def distance(c1, c2):
    return sqrt((c1.x - c2.x) ** 2 + (c1.y - c2.y) ** 2)


def component_text(component):
    return f"{component.ref} {component.type} {component.value}".lower()


def is_regulator(component, keywords):
    text = component_text(component)
    return any(keyword.lower() in text for keyword in keywords)


def is_load(component, keywords):
    text = component_text(component)
    return any(keyword.lower() in text for keyword in keywords)


def shared_nets(component_a, component_b):
    nets_a = {pad.net_name.upper() for pad in component_a.pads if pad.net_name}
    nets_b = {pad.net_name.upper() for pad in component_b.pads if pad.net_name}
    return nets_a & nets_b


def run_rule(pcb, config):
    risks = []
    rule_config = config.get("rules", {}).get("power_distribution", {})

    threshold = float(rule_config.get("threshold", 20.0))
    regulator_keywords = rule_config.get(
        "regulator_keywords",
        ["regulator", "ldo", "buck", "boost", "pmic", "vrm"]
    )
    load_keywords = rule_config.get(
        "load_keywords",
        ["mcu", "cpu", "fpga", "driver", "sensor", "ic", "controller", "amp"]
    )

    regulators = [c for c in pcb.components if is_regulator(c, regulator_keywords)]
    loads = [c for c in pcb.components if is_load(c, load_keywords)]

    if not regulators or not loads:
        return risks

    for load in loads:
        nearest_reg = None
        nearest_distance = None

        for reg in regulators:
            if reg.ref == load.ref:
                continue

            if load.pads and reg.pads:
                shared = shared_nets(load, reg)
                if not shared:
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
                    confidence=0.88 if load.pads and nearest_reg.pads else 0.76,
                    short_title="Weak power distribution path",
                    fix_priority="high",
                    estimated_impact="high",
                    design_domain="power",
                )
            )

    return risks