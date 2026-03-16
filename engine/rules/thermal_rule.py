import math

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