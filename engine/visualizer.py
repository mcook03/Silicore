import matplotlib.pyplot as plt


def draw_board(pcb, risks=None):
    if risks is None:
        risks = []

    risky_refs = set()

    for risk in risks:
        words = risk.replace(",", "").replace("[", "").replace("]", "").split()
        for word in words:
            if word.startswith(("R", "C", "U", "Q", "D", "L", "LED", "J", "SW")):
                risky_refs.add(word)

    x_safe, y_safe = [], []
    x_risk, y_risk = [], []

    for comp in pcb.components:
        if comp.ref in risky_refs:
            x_risk.append(comp.x)
            y_risk.append(comp.y)
        else:
            x_safe.append(comp.x)
            y_safe.append(comp.y)

    plt.figure(figsize=(10, 7))

    plt.scatter(x_safe, y_safe, label="Normal Components")
    plt.scatter(x_risk, y_risk, color="red", label="Risk Components")

    region_size = 10
    regions = {}

    for comp in pcb.components:
        rx = int(comp.x // region_size)
        ry = int(comp.y // region_size)
        key = (rx, ry)
        regions.setdefault(key, []).append(comp)

    for (rx, ry), comps in regions.items():
        count = len(comps)

        if count > 4:
            rect = plt.Rectangle(
                (rx * region_size, ry * region_size),
                region_size,
                region_size,
                color="orange",
                alpha=0.20
            )
            plt.gca().add_patch(rect)

    for comp in pcb.components:
        plt.text(comp.x + 0.2, comp.y + 0.2, comp.ref)

    plt.title("Silicore PCB Risk Visualization")
    plt.xlabel("X Position")
    plt.ylabel("Y Position")
    plt.grid(True)
    plt.legend()
    plt.show()