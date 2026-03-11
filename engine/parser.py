# engine/parser.py

from engine.pcb_model import PCB, Component


def start_engine():
    print("Silicore analysis engine initialized")


def parse_pcb_file(filename):
    pcb = PCB()

    with open(filename, "r") as file:
        lines = file.readlines()

    for line in lines[1:]:
        line = line.strip()

        if not line:
            continue

        parts = [item.strip() for item in line.split(",")]

        if len(parts) != 6:
            continue

        ref, value, x, y, layer, ctype = parts
        component = Component(ref, value, x, y, layer, ctype)
        pcb.add_component(component)

    return pcb