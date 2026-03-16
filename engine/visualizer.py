import matplotlib.pyplot as plt


def draw_board(pcb, risks=None):
    if risks is None:
        risks = []

    risky_refs = set()
    risky_regions = []

    for risk in risks:
        for ref in risk.get("components", []):
            risky_refs.add(ref)

        region = risk.get("region")
        if region:
            risky_regions.append(region)

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
    for region in risky_regions:
        rx, ry = region
        rect = plt.Rectangle(
            (rx, ry),
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