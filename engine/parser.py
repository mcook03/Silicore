from engine.pcb_model import PCB, Component


def start_engine():
    print("Silicore analysis engine initialized")


def link_nets_to_components(pcb):
    for component in pcb.components:
        component.connected_nets = []
        component.net_names = []
        component.net_name = ""
        component.net = ""

    for net_name, net in pcb.nets.items():
        for ref, pin in net.connections:
            component = pcb.get_component(ref)
            if not component:
                continue

            if net_name not in component.connected_nets:
                component.connected_nets.append(net_name)

    for component in pcb.components:
        unique_nets = []
        for net_name in component.connected_nets:
            clean_name = str(net_name).strip()
            if clean_name and clean_name not in unique_nets:
                unique_nets.append(clean_name)

        component.connected_nets = unique_nets
        component.net_names = list(unique_nets)
        component.net_name = unique_nets[0] if unique_nets else ""
        component.net = component.net_name


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

        link_nets_to_components(pcb)
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

    link_nets_to_components(pcb)
    pcb.estimate_board_bounds()
    return pcb