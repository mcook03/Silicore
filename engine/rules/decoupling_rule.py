from math import sqrt
from engine.risk import make_risk


def distance(c1, c2):
    return sqrt((c1.x - c2.x) ** 2 + (c1.y - c2.y) ** 2)


def component_text(component):
    return f"{component.ref} {component.type} {component.value}".lower()


def is_target_component(component, target_keywords):
    text = component_text(component)
    return any(keyword.lower() in text for keyword in target_keywords)


def is_capacitor(component, capacitor_keywords):
    text = component_text(component)

    if component.ref.upper().startswith("C"):
        return True

    return any(keyword.lower() in text for keyword in capacitor_keywords)


def shares_power_or_ground_net(component, other_component, power_ground_keywords):
    component_nets = {pad.net_name.upper() for pad in component.pads if pad.net_name}
    other_nets = {pad.net_name.upper() for pad in other_component.pads if pad.net_name}

    if not component_nets or not other_nets:
        return False

    shared = component_nets & other_nets

    for net in shared:
        if net in power_ground_keywords:
            return True

    return False


def run_rule(pcb, config):
    risks = []
    rule_config = config.get("rules", {}).get("decoupling", {})
    power_config = config.get("power", {})

    threshold = float(
        rule_config.get(
            "threshold",
            power_config.get("decoupling_distance_threshold", 4.0),
        )
    )
    target_keywords = rule_config.get(
        "target_keywords",
        ["mcu", "cpu", "fpga", "sensor", "driver", "ic", "controller"]
    )
    capacitor_keywords = rule_config.get(
        "capacitor_keywords",
        ["cap", "capacitor", "c"]
    )

    power_ground_keywords = {
        str(net).strip().upper()
        for net in (
            power_config.get("required_power_nets", ["VCC", "VIN", "VBAT", "5V", "3V3", "VDD"])
            + power_config.get("required_ground_nets", ["GND", "GROUND"])
        )
        if str(net).strip()
    }

    for comp in getattr(pcb, "components", []):
        if not is_target_component(comp, target_keywords):
            continue

        nearest_cap_distance = None
        nearest_cap = None

        for other in getattr(pcb, "components", []):
            if comp.ref == other.ref:
                continue

            if not is_capacitor(other, capacitor_keywords):
                continue

            if comp.pads and other.pads and not shares_power_or_ground_net(comp, other, power_ground_keywords):
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
                    trigger_condition="Nearest valid decoupling capacitor exceeded the configured decoupling distance threshold.",
                    threshold_label=f"Maximum decoupling distance {threshold:.2f} units",
                    observed_label=(
                        f"Observed nearest capacitor distance {nearest_cap_distance:.2f} units"
                        if nearest_cap_distance is not None
                        else "Observed nearest capacitor distance: none found"
                    ),
                )
            )

    return risks
