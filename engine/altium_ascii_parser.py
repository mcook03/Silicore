import re

from engine.pcb_model import PCB, Component, Pad, TraceSegment, Via


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _layer_name(value):
    text = str(value or "").strip()
    return text or "TopLayer"


def parse_altium_ascii_file(filepath):
    pcb = PCB(filename=filepath.split("/")[-1])
    pcb.source_format = "altium_ascii"

    component_map = {}
    current_component = None
    with open(filepath, "r", encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue

            upper = line.upper()
            if upper.startswith("RECORD=BOARD") or upper.startswith("BOARD"):
                continue

            if "LAYER" in upper:
                for match in re.findall(r"Layer(?:Name)?=([^|]+)", line, flags=re.IGNORECASE):
                    if match.strip():
                        pcb.add_layer(match.strip())

            if upper.startswith("RECORD=COMPONENT") or upper.startswith("COMPONENT"):
                ref = re.search(r"Designator=([^|]+)", line, flags=re.IGNORECASE)
                value = re.search(r"Comment=([^|]+)", line, flags=re.IGNORECASE)
                x = re.search(r"X=([^|]+)", line, flags=re.IGNORECASE)
                y = re.search(r"Y=([^|]+)", line, flags=re.IGNORECASE)
                layer = re.search(r"Layer(?:Name)?=([^|]+)", line, flags=re.IGNORECASE)
                ref_text = ref.group(1).strip() if ref else f"U{len(component_map) + 1}"
                component = Component(
                    ref=ref_text,
                    value=value.group(1).strip() if value else ref_text,
                    x=_safe_float(x.group(1)) if x else 0.0,
                    y=_safe_float(y.group(1)) if y else 0.0,
                    layer=_layer_name(layer.group(1) if layer else "TopLayer"),
                    comp_type="ic",
                )
                pcb.add_component(component)
                component_map[component.ref] = component
                current_component = component
                continue

            if upper.startswith("RECORD=PAD") or upper.startswith("PAD"):
                net = re.search(r"Net=([^|]+)", line, flags=re.IGNORECASE)
                name = re.search(r"Name=([^|]+)", line, flags=re.IGNORECASE)
                x = re.search(r"X=([^|]+)", line, flags=re.IGNORECASE)
                y = re.search(r"Y=([^|]+)", line, flags=re.IGNORECASE)
                layer = re.search(r"Layer(?:Name)?=([^|]+)", line, flags=re.IGNORECASE)
                pad = Pad(
                    component_ref=current_component.ref if current_component else "UNKNOWN",
                    pad_name=name.group(1).strip() if name else "1",
                    net_name=(net.group(1).strip().upper() if net else ""),
                    x=_safe_float(x.group(1)) if x else (current_component.x if current_component else 0.0),
                    y=_safe_float(y.group(1)) if y else (current_component.y if current_component else 0.0),
                    layer=_layer_name(layer.group(1) if layer else (current_component.layer if current_component else "TopLayer")),
                )
                if current_component:
                    current_component.add_pad(pad)
                if pad.net_name:
                    pcb.add_net_connection(pad.net_name, pad.component_ref, pad.pad_name)
                continue

            if upper.startswith("RECORD=TRACK") or upper.startswith("TRACK"):
                net = re.search(r"Net=([^|]+)", line, flags=re.IGNORECASE)
                x1 = re.search(r"X1=([^|]+)", line, flags=re.IGNORECASE)
                y1 = re.search(r"Y1=([^|]+)", line, flags=re.IGNORECASE)
                x2 = re.search(r"X2=([^|]+)", line, flags=re.IGNORECASE)
                y2 = re.search(r"Y2=([^|]+)", line, flags=re.IGNORECASE)
                width = re.search(r"Width=([^|]+)", line, flags=re.IGNORECASE)
                layer = re.search(r"Layer(?:Name)?=([^|]+)", line, flags=re.IGNORECASE)
                if not (net and x1 and y1 and x2 and y2):
                    continue
                segment = TraceSegment(
                    net_name=net.group(1).strip().upper(),
                    x1=_safe_float(x1.group(1)),
                    y1=_safe_float(y1.group(1)),
                    x2=_safe_float(x2.group(1)),
                    y2=_safe_float(y2.group(1)),
                    width=_safe_float(width.group(1), 0.2) if width else 0.2,
                    layer=_layer_name(layer.group(1) if layer else "TopLayer"),
                )
                pcb.add_trace_segment(segment.net_name, segment)
                continue

            if upper.startswith("RECORD=VIA") or upper.startswith("VIA"):
                net = re.search(r"Net=([^|]+)", line, flags=re.IGNORECASE)
                x = re.search(r"X=([^|]+)", line, flags=re.IGNORECASE)
                y = re.search(r"Y=([^|]+)", line, flags=re.IGNORECASE)
                hole = re.search(r"HoleSize=([^|]+)", line, flags=re.IGNORECASE)
                diameter = re.search(r"Size=([^|]+)", line, flags=re.IGNORECASE)
                via = Via(
                    net_name=(net.group(1).strip().upper() if net else ""),
                    x=_safe_float(x.group(1)) if x else 0.0,
                    y=_safe_float(y.group(1)) if y else 0.0,
                    drill=_safe_float(hole.group(1), 0.3) if hole else 0.3,
                    diameter=_safe_float(diameter.group(1), 0.6) if diameter else 0.6,
                    layers=[layer for layer in list(pcb.layers)[:2] or ["TopLayer", "BottomLayer"]],
                )
                if via.net_name:
                    pcb.add_via(via.net_name, via)
                continue

    if not pcb.layers:
        pcb.add_layers(["TopLayer", "BottomLayer"])
    return pcb
