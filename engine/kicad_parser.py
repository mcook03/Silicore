import re
from engine.pcb_model import PCB, Component, Pad, TraceSegment, Via


def parse_kicad_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    pcb = PCB(filename=filepath.split("/")[-1])

    net_id_to_name = parse_nets(content)
    parse_footprints(content, pcb)
    parse_segments(content, pcb, net_id_to_name)
    parse_vias(content, pcb, net_id_to_name)

    return pcb


def parse_nets(content):
    net_map = {}
    net_pattern = re.compile(r'\(net\s+(\d+)\s+"([^"]+)"\)')

    for match in net_pattern.finditer(content):
        net_id = match.group(1)
        net_name = match.group(2)
        net_map[net_id] = net_name

    return net_map


def parse_footprints(content, pcb):
    footprint_blocks = extract_blocks(content, "(footprint ")

    ref_pattern = re.compile(r'\(property\s+"Reference"\s+"([^"]+)"')
    value_pattern = re.compile(r'\(property\s+"Value"\s+"([^"]+)"')
    at_pattern = re.compile(r'\(at\s+([-\d\.]+)\s+([-\d\.]+)')
    layer_pattern = re.compile(r'\(layer\s+"([^"]+)"')
    pad_pattern = re.compile(
        r'\(pad\s+"?([^"\s]+)"?'
        r'.*?\(at\s+([-\d\.]+)\s+([-\d\.]+)'
        r'(?:\s+[-\d\.]+)?\)'
        r'.*?\(layers\s+([^)]+)\)'
        r'.*?\(net\s+\d+\s+"([^"]+)"\)',
        re.DOTALL
    )

    for block in footprint_blocks:
        ref_match = ref_pattern.search(block)
        value_match = value_pattern.search(block)
        at_match = at_pattern.search(block)
        layer_match = layer_pattern.search(block)

        if not ref_match or not at_match:
            continue

        ref = ref_match.group(1)
        value = value_match.group(1) if value_match else "unknown"
        x = float(at_match.group(1))
        y = float(at_match.group(2))
        layer = layer_match.group(1) if layer_match else "F.Cu"

        comp_type = infer_component_type(ref, value)
        component = Component(ref, value, x, y, layer=layer, comp_type=comp_type)

        for pad_match in pad_pattern.finditer(block):
            pad_name = pad_match.group(1)
            pad_dx = float(pad_match.group(2))
            pad_dy = float(pad_match.group(3))
            pad_layers = pad_match.group(4).strip().replace('"', "").split()
            net_name = pad_match.group(5)

            pad = Pad(
                component_ref=ref,
                pad_name=pad_name,
                net_name=net_name,
                x=x + pad_dx,
                y=y + pad_dy,
                layer=",".join(pad_layers),
            )

            component.add_pad(pad)
            pcb.add_net_connection(net_name, ref, pad_name)

        pcb.add_component(component)


def parse_segments(content, pcb, net_id_to_name):
    segment_pattern = re.compile(
        r'\(segment\s+'
        r'.*?\(start\s+([-\d\.]+)\s+([-\d\.]+)\)'
        r'.*?\(end\s+([-\d\.]+)\s+([-\d\.]+)\)'
        r'.*?\(width\s+([-\d\.]+)\)'
        r'.*?\(layer\s+"([^"]+)"\)'
        r'.*?\(net\s+(\d+)\)',
        re.DOTALL
    )

    for match in segment_pattern.finditer(content):
        x1 = match.group(1)
        y1 = match.group(2)
        x2 = match.group(3)
        y2 = match.group(4)
        width = match.group(5)
        layer = match.group(6)
        net_id = match.group(7)

        net_name = net_id_to_name.get(net_id)
        if not net_name:
            continue

        segment = TraceSegment(
            net_name=net_name,
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            width=width,
            layer=layer,
        )
        pcb.add_trace_segment(net_name, segment)


def parse_vias(content, pcb, net_id_to_name):
    via_pattern = re.compile(
        r'\(via\s+'
        r'.*?\(at\s+([-\d\.]+)\s+([-\d\.]+)\)'
        r'.*?\(size\s+([-\d\.]+)\)'
        r'.*?\(drill\s+([-\d\.]+)\)'
        r'.*?\(layers\s+([^)]+)\)'
        r'.*?\(net\s+(\d+)\)',
        re.DOTALL
    )

    for match in via_pattern.finditer(content):
        x = match.group(1)
        y = match.group(2)
        diameter = match.group(3)
        drill = match.group(4)
        layers = match.group(5).strip().replace('"', "").split()
        net_id = match.group(6)

        net_name = net_id_to_name.get(net_id)
        if not net_name:
            continue

        via = Via(
            net_name=net_name,
            x=x,
            y=y,
            drill=drill,
            diameter=diameter,
            layers=layers,
        )
        pcb.add_via(net_name, via)


def extract_blocks(content, start_token):
    blocks = []
    start_index = 0

    while True:
        start = content.find(start_token, start_index)
        if start == -1:
            break

        depth = 0
        end = start

        while end < len(content):
            char = content[end]

            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    end += 1
                    break

            end += 1

        blocks.append(content[start:end])
        start_index = end

    return blocks


def infer_component_type(ref, value):
    ref_upper = ref.upper()
    value_lower = str(value).lower()

    if ref_upper.startswith("R"):
        return "resistor"
    if ref_upper.startswith("C"):
        return "capacitor"
    if ref_upper.startswith("L"):
        return "inductor"
    if ref_upper.startswith("D"):
        return "diode"
    if ref_upper.startswith("Q"):
        return "transistor"
    if ref_upper.startswith("J"):
        return "connector"
    if ref_upper.startswith("U"):
        if any(word in value_lower for word in ["regulator", "ldo", "buck", "boost", "pmic"]):
            return "regulator"
        if any(word in value_lower for word in ["mcu", "cpu", "fpga", "controller", "driver", "sensor"]):
            return "ic"
        return "ic"

    return "unknown"