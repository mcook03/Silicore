import re

from engine.pcb_model import PCB, Component, Pad, Trace, Via, Zone


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _extract_quoted_or_unquoted_net_name(line):
    quoted = re.search(r'\(net_name\s+"([^"]+)"\)', line)
    if quoted:
        return quoted.group(1).strip()

    unquoted = re.search(r'\(net_name\s+([^\s)]+)\)', line)
    if unquoted:
        return unquoted.group(1).strip().replace('"', "")

    return ""


def parse_kicad_file(filename):
    pcb = PCB()
    pcb.source_format = "kicad_pcb"

    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    net_id_to_name = {}
    current_component = None
    current_component_x = 0.0
    current_component_y = 0.0
    current_component_layer = ""
    current_component_rotation = 0.0
    in_footprint = False

    for raw_line in lines:
        line = raw_line.strip()

        net_match = re.match(r'\(net\s+(\d+)\s+"?([^")]+)"?\)', line)
        if net_match:
            net_id = net_match.group(1)
            net_name = net_match.group(2).strip()
            net_id_to_name[net_id] = net_name
            if net_name not in pcb.nets:
                pcb.add_net_connection(net_name, "", "")
                pcb.nets[net_name].connections = []
            continue

        if line.startswith("(footprint "):
            in_footprint = True
            current_component = {
                "ref": "",
                "value": "",
                "footprint": line.replace("(footprint", "").strip().rstrip(")").strip('"'),
                "pads": [],
            }
            current_component_x = 0.0
            current_component_y = 0.0
            current_component_layer = ""
            current_component_rotation = 0.0
            continue

        if in_footprint and line.startswith("(at "):
            parts = line.replace("(", "").replace(")", "").split()
            if len(parts) >= 3:
                current_component_x = _safe_float(parts[1])
                current_component_y = _safe_float(parts[2])
            if len(parts) >= 4:
                current_component_rotation = _safe_float(parts[3])
            continue

        if in_footprint and line.startswith("(layer "):
            parts = line.replace("(", "").replace(")", "").split(maxsplit=1)
            if len(parts) == 2:
                current_component_layer = parts[1].replace('"', "")
            continue

        if in_footprint and "(property " in line and '"Reference"' in line:
            ref_match = re.search(r'"Reference"\s+"([^"]+)"', line)
            if ref_match:
                current_component["ref"] = ref_match.group(1)
            continue

        if in_footprint and "(property " in line and '"Value"' in line:
            value_match = re.search(r'"Value"\s+"([^"]+)"', line)
            if value_match:
                current_component["value"] = value_match.group(1)
            continue

        if in_footprint and line.startswith("(fp_text reference "):
            ref_match = re.search(r'\(fp_text reference\s+([^\s)]+)', line)
            if ref_match:
                current_component["ref"] = ref_match.group(1).replace('"', "")
            continue

        if in_footprint and line.startswith("(fp_text value "):
            value_match = re.search(r'\(fp_text value\s+([^\s)]+)', line)
            if value_match:
                current_component["value"] = value_match.group(1).replace('"', "")
            continue

        if in_footprint and line.startswith("(pad "):
            pad_parts = line.replace("(", "").replace(")", "").split()
            if len(pad_parts) >= 2 and current_component is not None:
                pad_number = pad_parts[1]

                at_match = re.search(r'\(at\s+([-\d.]+)\s+([-\d.]+)', raw_line)
                size_match = re.search(r'\(size\s+([-\d.]+)\s+([-\d.]+)\)', raw_line)
                layers_match = re.search(r'\(layers\s+([^)]+)\)', raw_line)
                net_inline_match = re.search(r'\(net\s+(\d+)\s+"?([^")]+)"?\)', raw_line)
                net_num_match = re.search(r'\(net\s+(\d+)', raw_line)

                pad_x = current_component_x
                pad_y = current_component_y
                if at_match:
                    pad_x = current_component_x + _safe_float(at_match.group(1))
                    pad_y = current_component_y + _safe_float(at_match.group(2))

                size_x = 0.0
                size_y = 0.0
                if size_match:
                    size_x = _safe_float(size_match.group(1))
                    size_y = _safe_float(size_match.group(2))

                layer = current_component_layer
                if layers_match:
                    layer = layers_match.group(1).strip().replace('"', "")

                net_name = ""
                if net_inline_match:
                    net_name = net_inline_match.group(2).strip()
                elif net_num_match:
                    net_id = net_num_match.group(1)
                    net_name = net_id_to_name.get(net_id, "")

                pad = Pad(
                    pad_number=pad_number,
                    x=pad_x,
                    y=pad_y,
                    net_name=net_name,
                    layer=layer,
                    size_x=size_x,
                    size_y=size_y,
                )
                current_component["pads"].append(pad)

                if net_name:
                    pcb.add_net_connection(net_name, current_component.get("ref", ""), pad_number)
            continue

        if line == ")" and in_footprint and current_component is not None:
            ref = current_component.get("ref", "").strip()
            value = current_component.get("value", "").strip()
            footprint = current_component.get("footprint", "").strip()

            if ref:
                comp_type = value if value else "unknown"
                component = Component(
                    ref=ref,
                    value=value if value else "unknown",
                    x=current_component_x,
                    y=current_component_y,
                    layer=current_component_layer,
                    comp_type=comp_type,
                    footprint=footprint,
                    rotation=current_component_rotation,
                )
                component.pads = current_component.get("pads", [])
                pcb.add_component(component)

            in_footprint = False
            current_component = None
            continue

        if line.startswith("(segment "):
            x1_match = re.search(r'\(start\s+([-\d.]+)\s+([-\d.]+)\)', line)
            x2_match = re.search(r'\(end\s+([-\d.]+)\s+([-\d.]+)\)', line)
            width_match = re.search(r'\(width\s+([-\d.]+)\)', line)
            layer_match = re.search(r'\(layer\s+"?([^")]+)"?\)', line)
            net_match = re.search(r'\(net\s+(\d+)\)', line)

            if x1_match and x2_match:
                x1 = _safe_float(x1_match.group(1))
                y1 = _safe_float(x1_match.group(2))
                x2 = _safe_float(x2_match.group(1))
                y2 = _safe_float(x2_match.group(2))
                width = _safe_float(width_match.group(1)) if width_match else 0.0
                layer = layer_match.group(1) if layer_match else ""
                net_name = ""
                if net_match:
                    net_name = net_id_to_name.get(net_match.group(1), "")
                pcb.add_trace(Trace(net_name, x1, y1, x2, y2, layer, width))
            continue

        if line.startswith("(via "):
            at_match = re.search(r'\(at\s+([-\d.]+)\s+([-\d.]+)\)', line)
            drill_match = re.search(r'\(drill\s+([-\d.]+)\)', line)
            size_match = re.search(r'\(size\s+([-\d.]+)\)', line)
            net_match = re.search(r'\(net\s+(\d+)\)', line)

            if at_match:
                x = _safe_float(at_match.group(1))
                y = _safe_float(at_match.group(2))
                drill = _safe_float(drill_match.group(1)) if drill_match else 0.0
                diameter = _safe_float(size_match.group(1)) if size_match else 0.0
                net_name = ""
                if net_match:
                    net_name = net_id_to_name.get(net_match.group(1), "")
                pcb.add_via(Via(x, y, drill, net_name, diameter))
            continue

        if line.startswith("(zone "):
            layer_match = re.search(r'\(layer\s+"?([^")]+)"?\)', line)
            layer = layer_match.group(1) if layer_match else ""
            net_name = _extract_quoted_or_unquoted_net_name(line)
            pcb.add_zone(Zone(net_name, layer))
            continue

    pcb.estimate_board_bounds()
    return pcb