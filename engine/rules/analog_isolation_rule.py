from math import sqrt

from engine.risk import make_risk


def _distance(x1, y1, x2, y2):
    return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def _upper_list(values):
    return [str(value).strip().upper() for value in (values or []) if str(value).strip()]


def _component_text(component):
    return f"{getattr(component, 'ref', '')} {getattr(component, 'value', '')} {getattr(component, 'type', '')} {getattr(component, 'footprint', '')}".upper()


def _matches_keywords(text, keywords):
    return any(keyword in text for keyword in keywords)


def _find_components(pcb, keywords):
    items = []
    for component in getattr(pcb, "components", []):
        if _matches_keywords(_component_text(component), keywords):
            items.append(component)
    return items


def _net_matches(net_name, keywords):
    return any(keyword in str(net_name or "").strip().upper() for keyword in keywords)


def run_rule(pcb, config):
    risks = []
    rule_config = config.get("rules", {}).get("analog_isolation", {})

    sensitive_keywords = _upper_list(
        rule_config.get(
            "sensitive_component_keywords",
            ["ADC", "DAC", "REF", "SENSOR", "OPAMP", "AFE", "AMP", "LNA", "ANALOG"],
        )
    )
    noisy_keywords = _upper_list(
        rule_config.get(
            "aggressor_component_keywords",
            ["REG", "BUCK", "BOOST", "PMIC", "INDUCTOR", "MOSFET", "SW", "USB", "ETH", "DDR", "MCU", "CPU"],
        )
    )
    analog_net_keywords = _upper_list(
        rule_config.get(
            "analog_net_keywords",
            ["ADC", "REF", "SENSE", "ANALOG", "VREF", "THERM", "CURRENT", "SHUNT"],
        )
    )
    sensitive_keepout = float(rule_config.get("sensitive_component_keepout", 8.0))
    max_analog_route_length = float(rule_config.get("max_analog_route_length", 20.0))

    sensitive_components = _find_components(pcb, sensitive_keywords)
    noisy_components = _find_components(pcb, noisy_keywords)

    for sensitive in sensitive_components:
        nearest_noisy = None
        for noisy in noisy_components:
            if noisy.ref == sensitive.ref:
                continue
            distance = _distance(sensitive.x, sensitive.y, noisy.x, noisy.y)
            if nearest_noisy is None or distance < nearest_noisy[1]:
                nearest_noisy = (noisy, distance)

        if nearest_noisy and nearest_noisy[1] < sensitive_keepout:
            aggressor = nearest_noisy[0]
            risks.append(
                make_risk(
                    rule_id="analog_isolation",
                    category="emi_emc",
                    severity="medium",
                    message=f"Sensitive analog component {sensitive.ref} sits close to noisy circuitry near {aggressor.ref}",
                    recommendation="Increase separation between the sensitive analog region and the noisy switching or digital circuitry, or improve shielding and return-path containment around the aggressor.",
                    components=[sensitive.ref, aggressor.ref],
                    nets=list({*getattr(sensitive, 'net_names', []), *getattr(aggressor, 'net_names', [])})[:4],
                    metrics={
                        "distance_to_aggressor": round(nearest_noisy[1], 2),
                        "keepout": sensitive_keepout,
                    },
                    confidence=0.8,
                    short_title="Weak analog-to-noisy isolation",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="emi",
                    why_it_matters="Sensitive analog circuitry placed too close to noisy digital or switching blocks is more likely to suffer coupling, reference corruption, or measurement instability.",
                    trigger_condition="A sensitive analog component fell inside the configured aggressor keepout distance.",
                    threshold_label=f"Minimum analog isolation distance {sensitive_keepout:.2f} units",
                    observed_label=f"Observed nearest aggressor distance {nearest_noisy[1]:.2f} units",
                )
            )

        analog_nets = [net for net in getattr(sensitive, "net_names", []) if _net_matches(net, analog_net_keywords)]
        for net_name in analog_nets[:3]:
            total_length = pcb.total_trace_length_for_net(net_name)
            if total_length > max_analog_route_length:
                risks.append(
                    make_risk(
                        rule_id="analog_isolation",
                        category="signal_integrity",
                        severity="medium",
                        message=f"Sensitive analog net {net_name} connected to {sensitive.ref} has a long routed path",
                        recommendation="Shorten the sensitive analog route, tighten placement around the analog chain, and reduce exposure to noisy regions or layer transitions.",
                        components=[sensitive.ref],
                        nets=[net_name],
                        metrics={
                            "trace_length": round(total_length, 2),
                            "max_analog_route_length": max_analog_route_length,
                        },
                        confidence=0.77,
                        short_title="Long sensitive analog route",
                        fix_priority="medium",
                        estimated_impact="moderate",
                        design_domain="signal_integrity",
                        why_it_matters="Long analog or reference routes are more exposed to noise pickup, impedance variation, and placement-related error.",
                        trigger_condition="A sensitive analog net exceeded the configured route-length threshold.",
                        threshold_label=f"Maximum sensitive analog route length {max_analog_route_length:.2f} units",
                        observed_label=f"Observed routed length {total_length:.2f} units",
                    )
                )

    return risks
