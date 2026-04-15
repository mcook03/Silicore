from math import sqrt

from engine.risk import make_risk


def _distance(x1, y1, x2, y2):
    return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def _component_text(component):
    return " ".join(
        [
            str(getattr(component, "ref", "")).strip(),
            str(getattr(component, "value", "")).strip(),
            str(getattr(component, "type", "")).strip(),
            str(getattr(component, "footprint", "")).strip(),
        ]
    ).upper()


def _matches_component(component, keywords):
    text = _component_text(component)
    return any(keyword in text for keyword in keywords)


def _component_nets(component):
    nets = []
    for pad in getattr(component, "pads", []):
        net_name = str(getattr(pad, "net_name", "")).strip().upper()
        if net_name and net_name not in nets:
            nets.append(net_name)
    return nets


def _unique_refs(*components):
    refs = []
    for component in components:
        ref = str(getattr(component, "ref", "")).strip()
        if ref and ref not in refs:
            refs.append(ref)
    return refs


def run_rule(pcb, config):
    risks = []
    rule_config = config.get("rules", {}).get("clock_sensitive_placement", {})

    clock_source_keywords = [
        str(item).strip().upper()
        for item in rule_config.get(
            "clock_source_keywords",
            ["XTAL", "OSC", "CRYSTAL", "CLOCK", "Y"],
        )
        if str(item).strip()
    ]
    controller_keywords = [
        str(item).strip().upper()
        for item in rule_config.get(
            "controller_keywords",
            ["MCU", "CPU", "SOC", "FPGA", "DSP", "STM", "ESP", "PIC", "AVR", "NRF", "IMX", "ATSAM"],
        )
        if str(item).strip()
    ]
    sensitive_keywords = [
        str(item).strip().upper()
        for item in rule_config.get(
            "sensitive_component_keywords",
            ["ADC", "DAC", "REF", "SENSOR", "OPAMP", "AMP", "LNA", "AFE", "ANALOG"],
        )
        if str(item).strip()
    ]
    aggressor_keywords = [
        str(item).strip().upper()
        for item in rule_config.get(
            "aggressor_component_keywords",
            ["REG", "BUCK", "BOOST", "PMIC", "INDUCTOR", "L", "MOSFET", "DRIVER", "SW", "CLOCK"],
        )
        if str(item).strip()
    ]

    max_clock_source_distance = float(rule_config.get("max_clock_source_distance", 12.0))
    sensitive_aggressor_keepout = float(rule_config.get("sensitive_aggressor_keepout", 8.0))

    clock_sources = [component for component in getattr(pcb, "components", []) if _matches_component(component, clock_source_keywords)]
    controllers = [component for component in getattr(pcb, "components", []) if _matches_component(component, controller_keywords)]
    sensitive_components = [component for component in getattr(pcb, "components", []) if _matches_component(component, sensitive_keywords)]
    aggressor_components = [component for component in getattr(pcb, "components", []) if _matches_component(component, aggressor_keywords)]

    for source in clock_sources:
        source_nets = set(_component_nets(source))
        nearest = None
        shared_net_match = False

        for controller in controllers:
            controller_nets = set(_component_nets(controller))
            distance = _distance(source.x, source.y, controller.x, controller.y)
            shares_clock_net = bool(source_nets & controller_nets)
            if shares_clock_net:
                shared_net_match = True
            rank = (0 if shares_clock_net else 1, distance)
            if nearest is None or rank < nearest[0]:
                nearest = (rank, controller, distance, shares_clock_net)

        if nearest is None:
            continue

        controller = nearest[1]
        distance = nearest[2]
        shares_clock_net = nearest[3]
        if distance > max_clock_source_distance:
            risks.append(
                make_risk(
                    rule_id="clock_sensitive_placement",
                    category="signal_integrity",
                    severity="high" if shares_clock_net else "medium",
                    message=f"Clock source {source.ref} is far from controller {controller.ref} ({distance:.2f} units)",
                    recommendation="Move the crystal or oscillator closer to the controller clock pins and keep the timing loop compact and isolated.",
                    components=_unique_refs(source, controller),
                    nets=sorted(list(source_nets))[:4],
                    metrics={
                        "distance": round(distance, 2),
                        "threshold": max_clock_source_distance,
                        "shares_clock_net": shares_clock_net,
                    },
                    confidence=0.84 if shares_clock_net else 0.74,
                    short_title="Clock source placement is weak",
                    fix_priority="high",
                    estimated_impact="high",
                    design_domain="signal_integrity",
                    why_it_matters="Oscillators and crystals work best when their loop to the controller is short, quiet, and physically compact.",
                    trigger_condition="A detected clock source was placed farther from the nearest likely controller than the configured timing-source distance threshold.",
                    threshold_label=f"Maximum clock-source distance {max_clock_source_distance:.2f} units",
                    observed_label=f"Observed source-to-controller distance {distance:.2f} units",
                )
            )

        if not shared_net_match and source_nets:
            risks.append(
                make_risk(
                    rule_id="clock_sensitive_placement",
                    category="signal_integrity",
                    severity="medium",
                    message=f"Clock source {source.ref} does not appear to share a direct clock net with the nearest controller",
                    recommendation="Confirm the crystal or oscillator is tied to the intended controller clock pins and that the timing loop is modeled clearly in layout.",
                    components=_unique_refs(source, controller),
                    nets=sorted(list(source_nets))[:4],
                    metrics={
                        "shared_clock_net": 0,
                        "controller_distance": round(distance, 2),
                    },
                    confidence=0.68,
                    short_title="Clock attachment is unclear",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="signal_integrity",
                    why_it_matters="Clock circuitry that is physically nearby but not clearly tied to the controller can indicate weak timing intent or incomplete routing.",
                    trigger_condition="A timing-source component was found without a clearly shared net to the nearest likely controller.",
                    threshold_label="Expected direct timing-net relationship between source and controller",
                    observed_label="Observed shared timing-net relationship: none",
                )
            )

    for sensitive in sensitive_components:
        nearest = None
        sensitive_nets = set(_component_nets(sensitive))

        for aggressor in aggressor_components:
            if aggressor is sensitive:
                continue
            distance = _distance(sensitive.x, sensitive.y, aggressor.x, aggressor.y)
            if nearest is None or distance < nearest[1]:
                nearest = (aggressor, distance)

        if nearest is None:
            continue

        aggressor = nearest[0]
        distance = nearest[1]
        if distance < sensitive_aggressor_keepout:
            aggressor_nets = set(_component_nets(aggressor))
            combined_nets = sorted(list((sensitive_nets | aggressor_nets)))[:4]
            risks.append(
                make_risk(
                    rule_id="clock_sensitive_placement",
                    category="signal_integrity",
                    severity="medium",
                    message=f"Sensitive component {sensitive.ref} sits close to noisy or switching circuitry near {aggressor.ref}",
                    recommendation="Increase separation, isolate the analog or timing-sensitive circuitry, or improve shielding and return-path quality around the aggressor region.",
                    components=_unique_refs(sensitive, aggressor),
                    nets=combined_nets,
                    metrics={
                        "distance": round(distance, 2),
                        "threshold": sensitive_aggressor_keepout,
                    },
                    confidence=0.78,
                    short_title="Sensitive placement near aggressor",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="signal_integrity",
                    why_it_matters="Sensitive analog and timing components are more vulnerable when placed too close to switching regulators, inductors, or other noisy circuitry.",
                    trigger_condition="A sensitive component fell inside the configured aggressor keepout window.",
                    threshold_label=f"Minimum sensitive-aggressor spacing {sensitive_aggressor_keepout:.2f} units",
                    observed_label=f"Observed sensitive-aggressor spacing {distance:.2f} units",
                )
            )

    return risks
