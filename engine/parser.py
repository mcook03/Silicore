from engine.pcb_model import PCB, Component


def start_engine():
    print("Silicore analysis engine initialized")


def parse_pcb_file(filename):
    pcb = PCB()
    pcb.source_format = "simple_text"

    with open(filename, "r") as file:
        lines = [line.strip() for line in file.readlines() if line.strip()]

    if not lines:
        return pcb

    if lines[0].startswith("ref,"):
        for line in lines[1:]:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) != 6:
                continue
            ref, value, x, y, layer, ctype = parts
            pcb.add_component(Component(ref, value, x, y, layer, ctype))
        pcb.estimate_board_bounds()
        return pcb

    section = None

    for line in lines:
        if line == "[COMPONENTS]":
            section = "components"
            continue

        if line == "[NETS]":
            section = "nets"
            continue

        if section == "components":
            if line.startswith("ref,"):
                continue

            parts = [p.strip() for p in line.split(",")]
            if len(parts) != 6:
                continue

            ref, value, x, y, layer, ctype = parts
            pcb.add_component(Component(ref, value, x, y, layer, ctype))

        elif section == "nets":
            if line.startswith("net,"):
                continue

            parts = [p.strip() for p in line.split(",")]
            if len(parts) != 3:
                continue

            net_name, ref, pin = parts
            pcb.add_net_connection(net_name, ref, pin)

    pcb.estimate_board_bounds()
    return pcb