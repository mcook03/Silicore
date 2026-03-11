import math


def check_component_spacing(pcb, min_distance=5):
    risks = []
    components = pcb.components

    for i in range(len(components)):
        for j in range(i + 1, len(components)):
            c1 = components[i]
            c2 = components[j]

            x1 = float(c1.x)
            y1 = float(c1.y)
            x2 = float(c2.x)
            y2 = float(c2.y)

            distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

            if distance < min_distance:
                risks.append(
                    f"Risk: {c1.ref} and {c2.ref} are too close ({distance:.2f} units)"
                )

    return risks


def check_decoupling_capacitors(pcb):
    risks = []

    microcontrollers = ["ATmega328", "STM32", "ESP32"]

    for comp in pcb.components:
        if comp.value in microcontrollers:
            mcu_x = comp.x
            mcu_y = comp.y

            capacitor_found = False

            for other in pcb.components:
                if "nF" in other.value or "uF" in other.value:
                    dx = other.x - mcu_x
                    dy = other.y - mcu_y
                    distance = (dx ** 2 + dy ** 2) ** 0.5

                    if distance < 5:
                        capacitor_found = True
                        break

            if not capacitor_found:
                risks.append(
                    f"Risk: {comp.ref} ({comp.value}) has no nearby decoupling capacitor"
                )

    return risks

def check_thermal_hotspots(pcb, min_distance=6):
    risks = []

    hot_types = ["REGULATOR", "MOSFET", "DRIVER", "POWER_IC"]

    hot_components = [comp for comp in pcb.components if comp.type in hot_types]

    for i in range(len(hot_components)):
        for j in range(i + 1, len(hot_components)):
            c1 = hot_components[i]
            c2 = hot_components[j]

            dx = c2.x - c1.x
            dy = c2.y - c1.y
            distance = (dx ** 2 + dy ** 2) ** 0.5

            if distance < min_distance:
                risks.append(
                    f"Risk: {c1.ref} and {c2.ref} may create a thermal hotspot ({distance:.2f} units)"
                )

    return risks

def check_component_density(pcb, region_size=10, max_components_per_region=4):
    risks = []
    regions = {}

    for component in pcb.components:
        region_x = int(component.x // region_size)
        region_y = int(component.y // region_size)
        region_key = (region_x, region_y)

        if region_key not in regions:
            regions[region_key] = []

        regions[region_key].append(component)

    for (region_x, region_y), components in regions.items():
        if len(components) > max_components_per_region:
            center_x = region_x * region_size
            center_y = region_y * region_size
            refs = ", ".join(c.ref for c in components)

            risks.append(
                f"Risk: High component density in region ({center_x},{center_y}) "
                f"with {len(components)} components [{refs}]"
            )

    return risks

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

    if score < 0:
        score = 0

    return round(score, 2)

def run_analysis(pcb):
    risks = []
    risks.extend(check_component_spacing(pcb))
    risks.extend(check_decoupling_capacitors(pcb))
    risks.extend(check_thermal_hotspots(pcb))
    risks.extend(check_component_density(pcb))

    score = calculate_risk_score(risks)

    return risks, score
