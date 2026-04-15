from engine.altium_ascii_parser import parse_altium_ascii_file
from engine.gerber_parser import parse_gerber_file
from engine.kicad_parser import parse_kicad_file
from engine.pcb_model import PCB, Component, Pad, TraceSegment, Via


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_layer(value):
    return str(value or "F.Cu").strip()


def _infer_component_type(ref, value, declared_type="unknown"):
    explicit = str(declared_type or "").strip().lower()
    if explicit and explicit != "unknown":
        return explicit

    ref_upper = str(ref or "").upper()
    value_lower = str(value or "").lower()

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
        return "ic"

    return "unknown"


def _ensure_component(pcb, ref, value="", x=0.0, y=0.0, layer="F.Cu", comp_type="unknown"):
    component = pcb.get_component(ref)
    if component is not None:
        return component

    component = Component(
        ref=ref,
        value=value or ref,
        x=_safe_float(x),
        y=_safe_float(y),
        layer=_normalize_layer(layer),
        comp_type=_infer_component_type(ref, value, comp_type),
    )
    pcb.add_component(component)
    return component


def parse_structured_board_file(filepath):
    pcb = PCB(filename=filepath.split("/")[-1])
    extension = filepath.rsplit(".", 1)[-1].lower() if "." in filepath else ""
    pcb.source_format = "legacy_brd" if extension == "brd" else "structured_text"

    with open(filepath, "r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split()
            keyword = parts[0].upper()

            if keyword == "BOARD" and len(parts) >= 2:
                pcb.filename = " ".join(parts[1:])

            elif keyword == "NET" and len(parts) >= 2:
                pcb.ensure_net(parts[1].strip().upper())

            elif keyword == "COMPONENT" and len(parts) >= 7:
                ref, value, x, y, layer, comp_type = parts[1:7]
                _ensure_component(
                    pcb,
                    ref=ref,
                    value=value,
                    x=x,
                    y=y,
                    layer=layer,
                    comp_type=comp_type,
                )

            elif keyword == "PAD" and len(parts) >= 7:
                component_ref, pad_name, net_name, dx, dy, layer, *rest = parts[1:]
                component = _ensure_component(pcb, component_ref, value=component_ref)
                pad = Pad(
                    component_ref=component_ref,
                    pad_name=pad_name,
                    net_name=net_name.strip().upper(),
                    x=component.x + _safe_float(dx),
                    y=component.y + _safe_float(dy),
                    layer=_normalize_layer(layer),
                )
                component.add_pad(pad)
                pcb.add_net_connection(pad.net_name, component_ref, pad_name)

            elif keyword == "CONNECT" and len(parts) >= 4:
                component_ref, net_name = parts[1], parts[2].strip().upper()
                pad_name = parts[3]
                component = _ensure_component(pcb, component_ref, value=component_ref)
                existing = [
                    pad for pad in component.pads
                    if pad.pad_name == pad_name and str(pad.net_name).upper() == net_name
                ]
                if not existing:
                    pad = Pad(
                        component_ref=component_ref,
                        pad_name=pad_name,
                        net_name=net_name,
                        x=component.x,
                        y=component.y,
                        layer=component.layer,
                    )
                    component.add_pad(pad)
                pcb.add_net_connection(net_name, component_ref, pad_name)

            elif keyword == "TRACE" and len(parts) >= 7:
                net_name, x1, y1, x2, y2, width, layer = parts[1:8]
                segment = TraceSegment(
                    net_name=net_name.strip().upper(),
                    x1=_safe_float(x1),
                    y1=_safe_float(y1),
                    x2=_safe_float(x2),
                    y2=_safe_float(y2),
                    width=_safe_float(width),
                    layer=_normalize_layer(layer),
                )
                pcb.add_trace_segment(segment.net_name, segment)

            elif keyword == "VIA" and len(parts) >= 6:
                net_name, x, y, drill, diameter, layers = parts[1:7]
                via = Via(
                    net_name=net_name.strip().upper(),
                    x=_safe_float(x),
                    y=_safe_float(y),
                    drill=_safe_float(drill),
                    diameter=_safe_float(diameter),
                    layers=[item.strip() for item in layers.split(",") if item.strip()],
                )
                pcb.add_via(via.net_name, via)

    return pcb


def parse_txt_pcb_file(filepath):
    return parse_structured_board_file(filepath)


def parse_brd_file(filepath):
    return parse_structured_board_file(filepath)


def parse_pcb_file(filepath):
    lower = filepath.lower()
    if lower.endswith(".kicad_pcb"):
        return parse_kicad_file(filepath)
    if lower.endswith(".gbr") or lower.endswith(".ger") or lower.endswith(".gko"):
        return parse_gerber_file(filepath)
    if lower.endswith(".pcbdocascii"):
        return parse_altium_ascii_file(filepath)
    if lower.endswith(".txt") or lower.endswith(".brd"):
        return parse_structured_board_file(filepath)

    raise ValueError(f"Unsupported PCB file format: {filepath}")
