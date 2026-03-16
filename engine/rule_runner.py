from engine.rules.spacing_rule import check_component_spacing
from engine.rules.decoupling_rule import check_decoupling_capacitors
from engine.rules.thermal_rule import check_thermal_hotspots
from engine.rules.density_rule import check_component_density
from engine.rules.power_distribution_rule import check_power_distribution
from engine.rules.power_rail_rule import check_power_rails
from engine.rules.signal_path_rule import check_signal_paths
from engine.rules.return_path_rule import check_return_paths


def calculate_risk_score(risks):
    score = 10.0

    for risk in risks:
        if "too close" in risk:
            score -= 1
        elif "decoupling capacitor" in risk:
            score -= 1.5
        elif "thermal hotspot" in risk:
            score -= 2
        elif "density" in risk:
            score -= 1
        elif "poor power delivery" in risk:
            score -= 1.5
        elif "power rail" in risk or "connected to the VOUT" in risk:
            score -= 1.5
        elif "signal path" in risk or "long signal path" in risk:
            score -= 1
        elif "return path" in risk or "No GND net found" in risk:
            score -= 1.5
        elif "ground connection" in risk:
            score -= 1.5

    if score < 0:
        score = 0

    return round(score, 2)


def run_analysis(pcb):
    risks = []

    rules = [
        check_component_spacing,
        check_decoupling_capacitors,
        check_thermal_hotspots,
        check_component_density,
        check_power_distribution,
        check_power_rails,
        check_signal_paths,
        check_return_paths,
    ]

    for rule in rules:
        risks.extend(rule(pcb))

    score = calculate_risk_score(risks)
    return risks, score