from math import sqrt

from engine.risk import make_risk


def _distance(x1, y1, x2, y2):
    return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def _upper_list(values):
    return [str(value).strip().upper() for value in (values or []) if str(value).strip()]


def _matches(net_name, keywords):
    upper = str(net_name or "").strip().upper()
    return any(keyword in upper for keyword in keywords)


def run_rule(pcb, config):
    risks = []
    rule_config = config.get("rules", {}).get("safety_high_voltage", {})

    high_voltage_keywords = _upper_list(
        rule_config.get(
            "high_voltage_net_keywords",
            ["HV", "VAC", "VDC", "VBUS", "48V", "24V", "PACK", "BATT"],
        )
    )
    min_clearance = float(rule_config.get("min_clearance", 2.5))
    min_creepage = float(rule_config.get("min_creepage", 5.0))

    hv_pads = []
    other_pads = []
    hv_components = {}

    for component in getattr(pcb, "components", []):
        for pad in getattr(component, "pads", []):
            net_name = str(getattr(pad, "net_name", "")).strip().upper()
            if not net_name:
                continue
            entry = (component.ref, net_name, pad)
            if _matches(net_name, high_voltage_keywords):
                hv_pads.append(entry)
                hv_components.setdefault(component.ref, set()).add(net_name)
            else:
                other_pads.append(entry)

    for component_ref, hv_nets in hv_components.items():
        component = pcb.get_component(component_ref)
        if component is None:
            continue

        nearest_other = None
        for other in getattr(pcb, "components", []):
            if other.ref == component_ref:
                continue
            distance = _distance(component.x, component.y, other.x, other.y)
            if nearest_other is None or distance < nearest_other[1]:
                nearest_other = (other, distance)

        if nearest_other and nearest_other[1] < min_creepage:
            risks.append(
                make_risk(
                    rule_id="safety_high_voltage",
                    category="safety_high_voltage",
                    severity="high",
                    message=f"High-voltage region around {component_ref} appears tightly packed for creepage assumptions",
                    recommendation="Increase physical separation, add slots or barriers where needed, and review the board against the intended voltage class and environment.",
                    components=[component_ref, nearest_other[0].ref],
                    nets=sorted(list(hv_nets))[:3],
                    metrics={
                        "nearest_component_distance": round(nearest_other[1], 2),
                        "min_creepage": min_creepage,
                    },
                    confidence=0.7,
                    short_title="Possible high-voltage creepage pressure",
                    fix_priority="high",
                    estimated_impact="high",
                    design_domain="safety",
                    why_it_matters="High-voltage regions need enough surface separation to reduce arcing and contamination-related failure risk.",
                    trigger_condition="A high-voltage component region fell inside the configured creepage spacing threshold.",
                    threshold_label=f"Minimum creepage spacing {min_creepage:.2f} units",
                    observed_label=f"Observed nearest component spacing {nearest_other[1]:.2f} units",
                )
            )

    for hv_ref, hv_net, hv_pad in hv_pads:
        nearest = None
        nearest_net = ""
        nearest_ref = ""
        for other_ref, other_net, other_pad in other_pads:
            distance = _distance(hv_pad.x, hv_pad.y, other_pad.x, other_pad.y)
            if nearest is None or distance < nearest:
                nearest = distance
                nearest_net = other_net
                nearest_ref = other_ref

        if nearest is not None and nearest < min_clearance:
            risks.append(
                make_risk(
                    rule_id="safety_high_voltage",
                    category="safety_high_voltage",
                    severity="critical",
                    message=f"High-voltage pad on {hv_ref}:{hv_net} is close to {nearest_ref}:{nearest_net}",
                    recommendation="Increase conductor spacing or introduce isolation features that meet the intended voltage-class clearance target.",
                    components=[hv_ref, nearest_ref],
                    nets=[hv_net, nearest_net],
                    metrics={
                        "clearance": round(nearest, 2),
                        "min_clearance": min_clearance,
                    },
                    confidence=0.83,
                    short_title="High-voltage clearance risk",
                    fix_priority="high",
                    estimated_impact="high",
                    design_domain="safety",
                    why_it_matters="Clearance shortfalls in elevated-voltage regions can create direct insulation and safety failures.",
                    trigger_condition="A high-voltage pad-to-pad spacing fell below the configured clearance threshold.",
                    threshold_label=f"Minimum clearance {min_clearance:.2f} units",
                    observed_label=f"Observed nearest clearance {nearest:.2f} units",
                )
            )

    return risks
