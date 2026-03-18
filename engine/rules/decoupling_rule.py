from math import sqrt

from engine.risk import make_risk


def distance(c1, c2):
    return sqrt((c1.x - c2.x) ** 2 + (c1.y - c2.y) ** 2)


def is_target_component(component, target_keywords):
    text = f"{component.type} {component.value} {component.ref}".lower()
    return any(keyword.lower() in text for keyword in target_keywords)


def is_capacitor(component, capacitor_keywords):
    text = f"{component.type} {component.value} {component.ref}".lower()

    if component.ref.upper().startswith("C"):
        return True

    return any(keyword.lower() in text for keyword in capacitor_keywords)


def shares_any_net(component, other_component):
    component_nets = {pad.net_name.upper() for pad in component.pads if pad.net_name}
    other_nets = {pad.net_name.upper() for pad in other_component.pads if pad.net_name}

    if not component_nets or not other_nets:
        return False

    return len(component_nets & other_nets) > 0


def run_rule(pcb, config):
    risks = []
    rule_config = config["rules"]["decoupling"]

    threshold = rule_config["threshold"]
    target_keywords = rule_config["target_keywords"]
    capacitor_keywords = rule_config["capacitor_keywords"]

    for comp in pcb.components:
        if not is_target_component(comp, target_keywords):
            continue

        nearest_cap_distance = None
        nearest_cap = None

        for other in pcb.components:
            if comp.ref == other.ref:
                continue

            if not is_capacitor(other, capacitor_keywords):
                continue

            if comp.pads and other.pads and not shares_any_net(comp, other):
                continue

            d = distance(comp, other)

            if nearest_cap_distance is None or d < nearest_cap_distance:
                nearest_cap_distance = d
                nearest_cap = other

        if nearest_cap_distance is None or nearest_cap_distance > threshold:
            risks.append(
                make_risk(
                    rule_id="decoupling",
                    category="power_integrity",
                    severity="medium",
                    message=f"{comp.ref} ({comp.value}) has no nearby decoupling capacitor",
                    recommendation="Place a decoupling capacitor close to the device power pin and on the relevant supply net.",
                    components=[comp.ref] + ([nearest_cap.ref] if nearest_cap else []),
                    metrics={
                        "nearest_cap_distance": round(nearest_cap_distance, 2) if nearest_cap_distance is not None else None,
                        "threshold": threshold,
                    },
                    confidence=0.9 if comp.pads else 0.8,
                    short_title="Missing nearby decoupling",
                    fix_priority="high",
                    estimated_impact="high",
                    design_domain="power",
                )
            )

    return risks