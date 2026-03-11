import matplotlib.pyplot as plt


def draw_board(pcb):
    x_coords = []
    y_coords = []
    labels = []

    for comp in pcb.components:
        x_coords.append(comp.x)
        y_coords.append(comp.y)
        labels.append(comp.ref)

    plt.figure(figsize=(8, 6))
    plt.scatter(x_coords, y_coords)

    for i, label in enumerate(labels):
        plt.text(x_coords[i] + 0.2, y_coords[i] + 0.2, label)

    plt.title("Silicore PCB Layout")
    plt.xlabel("X Position")
    plt.ylabel("Y Position")
    plt.grid(True)
    plt.show()