from engine.kicad_parser import parse_kicad_file


class Component:
    def __init__(self, ref, value, x, y, layer, comp_type):
        self.ref = ref
        self.value = value
        self.x = float(x)
        self.y = float(y)
        self.layer = layer
        self.type = comp_type


class PCB:
    def __init__(self, name="Unnamed Board"):
        self.name = name
        self.components = []
        self.nets = []

    def add_component(self, component):
        self.components.append(component)

    def add_net(self, net_name):
        if net_name not in self.nets:
            self.nets.append(net_name)


def parse_txt_pcb_file(filepath):
    pcb = PCB()

    with open(filepath, "r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split()

            if not parts:
                continue

            keyword = parts[0].upper()

            if keyword == "BOARD" and len(parts) >= 2:
                pcb.name = " ".join(parts[1:])

            elif keyword == "NET" and len(parts) >= 2:
                pcb.add_net(parts[1])

            elif keyword == "COMPONENT" and len(parts) >= 7:
                ref = parts[1]
                value = parts[2]
                x = parts[3]
                y = parts[4]
                layer = parts[5]
                comp_type = parts[6]
                pcb.add_component(Component(ref, value, x, y, layer, comp_type))

    return pcb


def parse_pcb_file(filepath):
    if filepath.endswith(".kicad_pcb"):
        return parse_kicad_file(filepath)

    if filepath.endswith(".txt"):
        return parse_txt_pcb_file(filepath)

    raise ValueError(f"Unsupported PCB file format: {filepath}")