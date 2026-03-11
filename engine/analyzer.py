import math

def check_component_spacing(components, min_distance=5):
    risks = []

    for i in range(len(components)):
        for j in range(i + 1, len(components)):
            c1 = components[i]
            c2 = components[j]

            x1 = float(c1['x'])
            y1 = float(c1['y'])
            x2 = float(c2['x'])
            y2 = float(c2['y'])

            distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

            if distance < min_distance:
                risks.append(
                    f"Risk: {c1['ref']} and {c2['ref']} are too close ({distance:.2f} units)"
                )

    return risks

def check_decoupling_capacitors(components):

    risks = []

    microcontrollers = ["ATmega328", "STM32", "ESP32"]

    for comp in components:

        if comp["value"] in microcontrollers:

            mcu_x = comp["x"]
            mcu_y = comp["y"]

            capacitor_found = False

            for other in components:

                if "nF" in other["value"] or "uF" in other["value"]:

                    dx = other["x"] - mcu_x
                    dy = other["y"] - mcu_y

                    distance = (dx**2 + dy**2) ** 0.5

                    if distance < 5:
                        capacitor_found = True

            if not capacitor_found:

                risks.append(
                    f"Risk: {comp['ref']} ({comp['value']}) has no nearby decoupling capacitor"
                )

    return risks