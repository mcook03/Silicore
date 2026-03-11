# engine/parser.py

from engine.pcb_model import PCB, Component

def start_engine():
    print("Silicore analysis engine initialized")


def parse_pcb_file(filename):
    pcb = PCB()

    with open(filename, "r") as file:
        lines = [line.strip() for line in file if line.strip()]

    for line in lines[1:]:
        parts = line.split(",")

        ref = parts[0]
        value = parts[1]
        x = int(parts[2])
        y = int(parts[3])
        layer = parts[4]

        component = Component(ref, value, x, y, layer)
        pcb.add_component(component)

    return pcb