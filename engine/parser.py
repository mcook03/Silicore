from engine.pcb_model import PCB, Component


def start_engine():
    print("Silicore analysis engine initialized")


def parse_pcb_file(filename):
    pcb = PCB()

    with open(filename, "r") as file:
        lines = [line.strip() for line in file.readlines() if line.strip()]

    section = None

    for line in lines:
        if line == "[COMPONENTS]":
            section = "components"
            continue
        elif line == "[NETS]":
            section = "nets"
            continue

        if section == "components":
            if line.startswith("ref,"):
                continue

            parts = [item.strip() for item in line.split(",")]
            if len(parts) != 6:
                continue

            ref, value, x, y, layer, ctype = parts
            component = Component(ref, value, x, y, layer, ctype)
            pcb.add_component(component)

        elif section == "nets":
            if line.startswith("net,"):
                continue

            parts = [item.strip() for item in line.split(",")]
            if len(parts) != 3:
                continue

            net_name, ref, pin = parts
            pcb.add_net_connection(net_name, ref, pin)

    return pcb