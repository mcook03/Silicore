import matplotlib.pyplot as plt


def draw_board(pcb, risks=None):
    if risks is None:
        risks = []

    risky_refs = set()

    # Identify risky components mentioned in risks
    for risk in risks:
        words = risk.replace(",", "").split()
        for word in words:
            if word.startswith(("R", "C", "U", "Q", "D", "L", "LED")):
                risky_refs.add(word)

    x_safe = []
    y_safe = []

    x_risk = []
    y_risk = []

    for comp in pcb.components:
        if comp.ref in risky_refs:
            x_risk.append(comp.x)
            y_risk.append(comp.y)
        else:
            x_safe.append(comp.x)
            y_safe.append(comp.y)

    plt.figure(figsize=(8, 6))

    # Safe components
    plt.scatter(x_safe, y_safe, label="Normal Components")

    # Risky components
    plt.scatter(x_risk, y_risk, color="red", label="Risk Components")

    # Highlight crowded regions (component density)
    region_size = 10
    regions = {}

    for comp in pcb.components:
        region_x = int(comp.x // region_size)
        region_y = int(comp.y // region_size)

        key = (region_x, region_y)

        if key not in regions:
            regions[key] = []

        regions[key].append(comp)

    for (rx, ry), comps in regions.items():
        if len(comps) > 4:
            center_x = rx * region_size
            center_y = ry * region_size

            plt.gca().add_patch(
                plt.Rectangle(
                    (center_x, center_y),
                    region_size,
                    region_size,
                    fill=False,
                    edgecolor="orange",
                    linewidth=2
                )
            )

    # Labels
    for comp in pcb.components:
        plt.text(comp.x + 0.2, comp.y + 0.2, comp.ref)

    plt.title("Silicore PCB Layout Analysis")
    plt.xlabel("X Position")
    plt.ylabel("Y Position")

    plt.legend()
    plt.grid(True)
    plt.show()