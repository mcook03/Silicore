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