import os
import re

from engine.kicad_parser import extract_blocks, infer_component_type
from engine.pcb_model import PCB, Component, Pad, TraceSegment


def parse_kicad_schematic_file(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        content = file.read()

    pcb = PCB(filename=os.path.basename(filepath))
    pcb.source_format = "kicad_schematic"
    pcb.add_layer("Schematic")

    library_symbols = _parse_library_symbols(content)
    symbol_instances = _parse_symbol_instances(content, library_symbols)
    wires = _parse_wires(content)
    labels = _parse_labels(content)
    sheet_pins = _parse_sheet_pins(content)
    junctions = _parse_junctions(content)

    for component in symbol_instances:
        pcb.add_component(component)

    _attach_nets_and_wires(
        pcb=pcb,
        wires=wires,
        labels=labels,
        sheet_pins=sheet_pins,
        junctions=junctions,
    )
    pcb.merge_metadata(
        "parser",
        {
            "kind": "kicad_schematic",
            "library_symbol_count": len(library_symbols),
            "component_count": len(symbol_instances),
            "wire_count": len(wires),
            "label_count": len(labels),
            "sheet_pin_count": len(sheet_pins),
            "junction_count": len(junctions),
        },
    )
    pcb.merge_metadata(
        "schematic",
        {
            "active": True,
            "library_symbol_count": len(library_symbols),
            "component_count": len(symbol_instances),
            "wire_count": len(wires),
            "label_count": len(labels),
            "sheet_pin_count": len(sheet_pins),
            "junction_count": len(junctions),
            "net_count": len(pcb.nets),
            "summary": (
                f"KiCad schematic import recognized {len(symbol_instances)} symbols, "
                f"{len(pcb.nets)} nets, and {len(wires)} wire segment(s)."
            ),
        },
    )
    pcb.estimate_board_bounds()
    return pcb


def _parse_library_symbols(content):
    lib_blocks = extract_blocks(content, "(lib_symbols")
    if not lib_blocks:
        return {}

    library_symbols = {}
    for block in extract_blocks(lib_blocks[0], '(symbol "'):
        if '(property "Reference"' not in block:
            continue
        first_line = block.splitlines()[0]
        lib_id_match = re.match(r'\(symbol\s+"([^"]+)"', first_line.strip())
        if not lib_id_match:
            continue
        lib_id = lib_id_match.group(1)
        pins = []
        for pin_block in extract_blocks(block, "(pin "):
            at_match = re.search(r'\(at\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\)', pin_block)
            number_match = re.search(r'\(number\s+"([^"]+)"', pin_block)
            name_match = re.search(r'\(name\s+"([^"]*)"', pin_block)
            if not at_match or not number_match:
                continue
            pins.append(
                {
                    "number": number_match.group(1),
                    "name": name_match.group(1) if name_match else "",
                    "x": float(at_match.group(1)),
                    "y": float(at_match.group(2)),
                    "rotation": float(at_match.group(3)),
                }
            )
        library_symbols[lib_id] = pins
    return library_symbols


def _parse_symbol_instances(content, library_symbols):
    symbol_blocks = extract_blocks(content, "(symbol (lib_id")
    components = []
    property_pattern = re.compile(r'\(property\s+"([^"]+)"\s+"([^"]*)"')
    instance_pin_pattern = re.compile(r'\(pin\s+"([^"]+)"\s+\(uuid\s+([^)]+)\)\)')

    for block in symbol_blocks:
        lib_id_match = re.search(r'\(lib_id\s+"([^"]+)"\)', block)
        at_match = re.search(r'\(at\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\)', block)
        if not lib_id_match or not at_match:
            continue

        properties = {name: value for name, value in property_pattern.findall(block)}
        ref = properties.get("Reference", "").strip()
        if not ref or ref.startswith("#"):
            continue

        value = properties.get("Value", ref)
        footprint = properties.get("Footprint", "")
        x = float(at_match.group(1))
        y = float(at_match.group(2))
        rotation = float(at_match.group(3))
        mirror_x = "(mirror x)" in block
        mirror_y = "(mirror y)" in block
        lib_id = lib_id_match.group(1)

        component = Component(
            ref=ref,
            value=value,
            x=x,
            y=y,
            layer="Schematic",
            comp_type=infer_component_type(ref, value),
            footprint=footprint,
            rotation=rotation,
        )

        library_pin_map = {item["number"]: item for item in library_symbols.get(lib_id, [])}
        instance_pins = instance_pin_pattern.findall(block)
        pin_numbers = [pin_number for pin_number, _ in instance_pins] or list(library_pin_map.keys())

        for pin_number in pin_numbers:
            pin_def = library_pin_map.get(pin_number)
            if not pin_def:
                continue
            pad_x, pad_y = _transform_pin(pin_def["x"], pin_def["y"], x, y, rotation, mirror_x, mirror_y)
            component.add_pad(
                Pad(
                    component_ref=ref,
                    pad_name=pin_number,
                    net_name=None,
                    x=pad_x,
                    y=pad_y,
                    layer="Schematic",
                )
            )

        components.append(component)
    return components


def _parse_wires(content):
    wires = []
    for block in extract_blocks(content, "(wire "):
        points = re.findall(r'\(xy\s+([-\d.]+)\s+([-\d.]+)\)', block)
        if len(points) < 2:
            continue
        (x1, y1), (x2, y2) = points[:2]
        wires.append((_point_key(float(x1), float(y1)), _point_key(float(x2), float(y2))))
    return wires


def _parse_labels(content):
    labels = []
    for token in ("label", "global_label", "hierarchical_label"):
        pattern = re.compile(rf'\({token}\s+"([^"]+)"\s+(?:\(shape\s+[^\)]+\)\s+)?\(at\s+([-\d.]+)\s+([-\d.]+)\s+[-\d.]+\)')
        for name, x, y in pattern.findall(content):
            labels.append({"name": name, "point": _point_key(float(x), float(y)), "kind": token})
    return labels


def _parse_sheet_pins(content):
    pins = []
    for sheet_block in extract_blocks(content, "(sheet "):
        for match in re.finditer(r'\(pin\s+"([^"]+)"\s+[^\(]*\(at\s+([-\d.]+)\s+([-\d.]+)\s+[-\d.]+\)', sheet_block):
            pins.append({"name": match.group(1), "point": _point_key(float(match.group(2)), float(match.group(3))), "kind": "sheet_pin"})
    return pins


def _parse_junctions(content):
    return [
        _point_key(float(x), float(y))
        for x, y in re.findall(r'\(junction\s+\(at\s+([-\d.]+)\s+([-\d.]+)\)', content)
    ]


def _attach_nets_and_wires(pcb, wires, labels, sheet_pins, junctions):
    nodes = set(junctions)
    label_names_by_point = {}
    anchor_names_by_point = {}

    for component in pcb.components:
        for pad in component.pads:
            nodes.add(_point_key(pad.x, pad.y))

    for point_a, point_b in wires:
        nodes.add(point_a)
        nodes.add(point_b)

    for item in labels:
        nodes.add(item["point"])
        label_names_by_point.setdefault(item["point"], []).append(item["name"])
        anchor_names_by_point.setdefault(item["point"], []).append(item["name"])

    for item in sheet_pins:
        nodes.add(item["point"])
        anchor_names_by_point.setdefault(item["point"], []).append(item["name"])

    adjacency = {point: set() for point in nodes}
    traced_segments = []
    for point_a, point_b in wires:
        segment_nodes = [point for point in nodes if _point_on_segment(point, point_a, point_b)]
        segment_nodes = _sort_points_along_segment(segment_nodes, point_a, point_b)
        for start, end in zip(segment_nodes, segment_nodes[1:]):
            adjacency.setdefault(start, set()).add(end)
            adjacency.setdefault(end, set()).add(start)
            traced_segments.append((start, end))

    point_to_component_pads = {}
    for component in pcb.components:
        for pad in component.pads:
            point_to_component_pads.setdefault(_point_key(pad.x, pad.y), []).append((component, pad))

    visited = set()
    auto_index = 1
    point_to_net_name = {}
    for start_point in nodes:
        if start_point in visited:
            continue
        stack = [start_point]
        cluster = []
        while stack:
            point = stack.pop()
            if point in visited:
                continue
            visited.add(point)
            cluster.append(point)
            for neighbor in adjacency.get(point, ()):
                if neighbor not in visited:
                    stack.append(neighbor)

        names = []
        for point in cluster:
            for name in anchor_names_by_point.get(point, []):
                if name not in names:
                    names.append(name)
        net_name = names[0] if names else f"SCHEMATIC_NET_{auto_index}"
        auto_index += 1
        for point in cluster:
            point_to_net_name[point] = net_name

        for point in cluster:
            for component, pad in point_to_component_pads.get(point, []):
                pad.net_name = net_name
                component.sync_nets_from_pads()
                pcb.add_net_connection(net_name, component.ref, pad.pad_name)

    for start, end in traced_segments:
        net_name = point_to_net_name.get(start) or point_to_net_name.get(end)
        if not net_name:
            continue
        pcb.add_trace_segment(
            net_name,
            TraceSegment(
                net_name=net_name,
                x1=start[0],
                y1=start[1],
                x2=end[0],
                y2=end[1],
                width=0.0,
                layer="Schematic",
            ),
        )


def _transform_pin(local_x, local_y, origin_x, origin_y, rotation, mirror_x, mirror_y):
    x = -local_x if mirror_x else local_x
    y = -local_y if mirror_y else local_y

    rotation_key = int(round(rotation)) % 360
    if rotation_key == 90:
        x, y = -y, x
    elif rotation_key == 180:
        x, y = -x, -y
    elif rotation_key == 270:
        x, y = y, -x

    return origin_x + x, origin_y + y


def _point_key(x, y):
    return round(float(x), 4), round(float(y), 4)


def _point_on_segment(point, start, end, tolerance=1e-4):
    px, py = point
    x1, y1 = start
    x2, y2 = end
    if abs(x1 - x2) <= tolerance:
        if abs(px - x1) > tolerance:
            return False
        return min(y1, y2) - tolerance <= py <= max(y1, y2) + tolerance
    if abs(y1 - y2) <= tolerance:
        if abs(py - y1) > tolerance:
            return False
        return min(x1, x2) - tolerance <= px <= max(x1, x2) + tolerance
    cross = abs((px - x1) * (y2 - y1) - (py - y1) * (x2 - x1))
    if cross > tolerance:
        return False
    return (
        min(x1, x2) - tolerance <= px <= max(x1, x2) + tolerance
        and min(y1, y2) - tolerance <= py <= max(y1, y2) + tolerance
    )


def _sort_points_along_segment(points, start, end):
    if abs(start[0] - end[0]) >= abs(start[1] - end[1]):
        return sorted(set(points), key=lambda point: (point[0], point[1]))
    return sorted(set(points), key=lambda point: (point[1], point[0]))
