import matplotlib.pyplot as plt


def draw_board(pcb, risks=None):
    if risks is None:
        risks = []

    x_safe = []
    y_safe = []

    x_risk = []
    y_risk = []

    labels = []

    risky_refs = set()

    # Extract component references from risk messages
    for risk in risks:
        words = risk.split()
        for word in words:
            if word.startswith(("R", "C", "U", "Q", "D", "L", "LED")):
                risky_refs.add(word)

    for comp in pcb.components:
        if comp.ref in risky_refs:
            x_risk.append(comp.x)
            y_risk.append(comp.y)
        else:
            x_safe.append(comp.x)
            y_safe.append(comp.y)

        labels.append((comp.ref, comp.x, comp.y))

    plt.figure(figsize=(8, 6))

    # Safe components
    plt.scatter(x_safe, y_safe, label="Normal Components")

    # Risk components
    plt.scatter(x_risk, y_risk, color="red", label="Risk Components")

    for label, x, y in labels:
        plt.text(x + 0.2, y + 0.2, label)

    plt.title("Silicore PCB Layout Analysis")
    plt.xlabel("X Position")
    plt.ylabel("Y Position")

    plt.legend()
    plt.grid(True)
    plt.show()