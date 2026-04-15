from math import sqrt

from engine.risk import make_risk


def _distance(component, via):
    return sqrt((component.x - via.x) ** 2 + (component.y - via.y) ** 2)


def _connected_net_names(component):
    nets = set()
    for pad in getattr(component, "pads", []):
        if getattr(pad, "net_name", None):
            nets.add(str(pad.net_name).strip().upper())
    return nets


def run_rule(pcb, config):
    risks = []
    rule_config = config.get("rules", {}).get("thermal_management", {})
    power_config = config.get("power", {})

    hot_keywords = [str(item).strip().lower() for item in rule_config.get(
        "hot_component_keywords",
        ["regulator", "buck", "boost", "ldo", "pmic", "mosfet", "driver", "diode", "inductor", "power"],
    )]
    thermal_via_radius = float(rule_config.get("thermal_via_radius", 4.0))
    min_thermal_vias = int(rule_config.get("min_thermal_vias", 1))
    min_heat_spread_width = float(rule_config.get("min_heat_spread_width", power_config.get("min_trace_width", 0.5)))

    for component in getattr(pcb, "components", []):
        text = f"{getattr(component, 'ref', '')} {getattr(component, 'type', '')} {getattr(component, 'value', '')}".lower()
        if not any(keyword in text for keyword in hot_keywords):
            continue

        component_nets = _connected_net_names(component)
        nearby_vias = []
        connected_widths = []

        for via in getattr(pcb, "vias", []):
            if component_nets and str(via.net_name).strip().upper() not in component_nets:
                continue
            if _distance(component, via) <= thermal_via_radius:
                nearby_vias.append(via)

        for net_name in component_nets:
            net = getattr(pcb, "nets", {}).get(net_name)
            if not net:
                continue
            for segment in getattr(net, "trace_segments", []):
                connected_widths.append(float(getattr(segment, "width", 0.0)))

        if len(nearby_vias) < min_thermal_vias:
            risks.append(
                make_risk(
                    rule_id="thermal_management",
                    category="thermal",
                    severity="medium",
                    message=f"{component.ref} appears to have limited nearby thermal via support ({len(nearby_vias)})",
                    recommendation="Add thermal vias or improve heat escape near this power-dissipating component.",
                    components=[component.ref],
                    nets=sorted(component_nets),
                    metrics={
                        "nearby_thermal_vias": len(nearby_vias),
                        "threshold": min_thermal_vias,
                        "radius": thermal_via_radius,
                    },
                    confidence=0.8,
                    short_title="Limited thermal-via support",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="thermal",
                    why_it_matters="Power-dissipating parts often need nearby thermal vias to move heat into more copper area or additional layers.",
                    trigger_condition="Nearby thermal-via count fell below the configured heat-exit support threshold.",
                    threshold_label=f"Minimum nearby thermal vias {min_thermal_vias}",
                    observed_label=f"Observed nearby thermal vias {len(nearby_vias)}",
                )
            )

        if connected_widths and max(connected_widths) < min_heat_spread_width:
            max_width = max(connected_widths)
            risks.append(
                make_risk(
                    rule_id="thermal_management",
                    category="thermal",
                    severity="medium",
                    message=f"{component.ref} connects to relatively narrow copper for heat spreading ({max_width:.2f})",
                    recommendation="Increase local copper width or area around this component to improve heat spreading.",
                    components=[component.ref],
                    nets=sorted(component_nets),
                    metrics={
                        "max_connected_width": round(max_width, 3),
                        "threshold": min_heat_spread_width,
                    },
                    confidence=0.76,
                    short_title="Weak local heat spreading",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="thermal",
                    why_it_matters="Narrow connected copper can limit heat spreading and increase hotspot risk around power components.",
                    trigger_condition="Connected copper width fell below the configured thermal spreading threshold.",
                    threshold_label=f"Minimum heat-spread width {min_heat_spread_width:.2f}",
                    observed_label=f"Observed heat-spread width {max_width:.2f}",
                )
            )

    return risks
