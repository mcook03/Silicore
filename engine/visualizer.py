import matplotlib.pyplot as plt


def draw_board(pcb, risks=None):
    if risks is None:
        risks = []

    severity_order = {
        "low": 1,
        "medium": 2,
        "high": 3,
        "critical": 4,
    }

    severity_colors = {
        "low": "yellow",
        "medium": "orange",
        "high": "red",
        "critical": "darkred",
        "safe": "blue",
    }

    component_severity = {}

    # Find the highest severity attached to each component
    for risk in risks:
        severity = risk.get("severity", "medium")
        components = risk.get("components", [])

        for ref in components:
            current = component_severity.get(ref)

            if current is None or severity_order[severity] > severity_order[current]:
                component_severity[ref] = severity

    plt.figure(figsize=(10, 7))

    # Plot components one by one so each can have its own color
    for comp in pcb.components:
        severity = component_severity.get(comp.ref, "safe")
        color = severity_colors[severity]

        plt.scatter(comp.x, comp.y, color=color)

        plt.text(comp.x + 0.2, comp.y + 0.2, comp.ref)

    # Draw risky regions if provided
    drawn_regions = set()
    region_size = 10

    for risk in risks:
        region = risk.get("region")
        severity = risk.get("severity", "medium")

        if region and region not in drawn_regions:
            drawn_regions.add(region)

            rx, ry = region
            rect = plt.Rectangle(
                (rx, ry),
                region_size,
                region_size,
                color=severity_colors.get(severity, "orange"),
                alpha=0.20,
            )
            plt.gca().add_patch(rect)

    # Legend
    plt.scatter([], [], color="blue", label="Safe")
    plt.scatter([], [], color="yellow", label="Low Risk")
    plt.scatter([], [], color="orange", label="Medium Risk")
    plt.scatter([], [], color="red", label="High Risk")
    plt.scatter([], [], color="darkred", label="Critical Risk")

    plt.title("Silicore PCB Severity Visualization")
    plt.xlabel("X Position")
    plt.ylabel("Y Position")
    plt.grid(True)
    plt.legend()
    plt.show()