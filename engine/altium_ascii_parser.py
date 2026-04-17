import re

from engine.pcb_model import PCB, Component, OutlineSegment, Pad, TraceSegment, Via, Zone


def _safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        text = str(value).strip()
        if not text:
            return default
        match = re.search(r"[-+]?\d*\.?\d+", text.replace(",", ""))
        return float(match.group(0)) if match else default
    except (TypeError, ValueError):
        return default


def _layer_name(value):
    text = str(value or "").strip()
    return text or "TopLayer"


def _parse_fields(line):
    fields = {}
    for token in str(line).split("|"):
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        fields[key.strip().lower()] = value.strip()
    return fields


def _record_type(line):
    match = re.search(r"RECORD=([^|]+)", line, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip().lower()
    return str(line).split("|", 1)[0].strip().lower()


def _field(fields, *names):
    for name in names:
        value = fields.get(name)
        if value not in {None, ""}:
            return value
    return None


def parse_altium_ascii_file(filepath):
    pcb = PCB(filename=filepath.split("/")[-1])
    pcb.source_format = "altium_ascii"

    component_map = {}
    current_component = None
    pending_region_points = []
    with open(filepath, "r", encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue

            upper = line.upper()
            fields = _parse_fields(line)
            record_type = _record_type(line)
            if record_type == "board" or upper == "BOARD":
                continue

            if "LAYER" in upper:
                for match in re.findall(r"Layer(?:Name)?=([^|]+)", line, flags=re.IGNORECASE):
                    if match.strip():
                        pcb.add_layer(match.strip())

            if record_type == "component" or upper.startswith("COMPONENT"):
                ref_text = _field(fields, "designator", "refdes", "name") or f"U{len(component_map) + 1}"
                component = Component(
                    ref=ref_text,
                    value=_field(fields, "comment", "value", "footprint") or ref_text,
                    x=_safe_float(_field(fields, "x", "locationx")),
                    y=_safe_float(_field(fields, "y", "locationy")),
                    layer=_layer_name(_field(fields, "layername", "layer") or "TopLayer"),
                    comp_type="ic",
                )
                pcb.add_component(component)
                component_map[component.ref] = component
                current_component = component
                continue

            if record_type in {"pad", "padstack"} or upper.startswith("PAD"):
                component_ref = _field(fields, "component", "componentref", "designator") or (current_component.ref if current_component else "UNKNOWN")
                component = component_map.get(component_ref)
                if component is None:
                    component = Component(
                        ref=component_ref,
                        value=component_ref,
                        x=_safe_float(_field(fields, "x", "locationx")),
                        y=_safe_float(_field(fields, "y", "locationy")),
                        layer=_layer_name(_field(fields, "layername", "layer") or "TopLayer"),
                        comp_type="unknown",
                    )
                    pcb.add_component(component)
                    component_map[component_ref] = component
                pad = Pad(
                    component_ref=component_ref,
                    pad_name=_field(fields, "name", "pad", "number") or "1",
                    net_name=((_field(fields, "net", "netname") or "").strip().upper()),
                    x=_safe_float(_field(fields, "x", "locationx")) if _field(fields, "x", "locationx") is not None else component.x,
                    y=_safe_float(_field(fields, "y", "locationy")) if _field(fields, "y", "locationy") is not None else component.y,
                    layer=_layer_name(_field(fields, "layername", "layer") or component.layer),
                    size_x=_safe_float(_field(fields, "sizex", "size", "xsize", "diameter")),
                    size_y=_safe_float(_field(fields, "sizey", "size", "ysize", "diameter")),
                )
                component.add_pad(pad)
                if pad.net_name:
                    pcb.add_net_connection(pad.net_name, pad.component_ref, pad.pad_name)
                continue

            if record_type in {"track", "tracks", "line"} or upper.startswith("TRACK"):
                if not all(_field(fields, *keys) is not None for keys in (("net", "netname"), ("x1", "xstart"), ("y1", "ystart"), ("x2", "xend"), ("y2", "yend"))):
                    continue
                segment = TraceSegment(
                    net_name=(_field(fields, "net", "netname") or "").strip().upper(),
                    x1=_safe_float(_field(fields, "x1", "xstart")),
                    y1=_safe_float(_field(fields, "y1", "ystart")),
                    x2=_safe_float(_field(fields, "x2", "xend")),
                    y2=_safe_float(_field(fields, "y2", "yend")),
                    width=_safe_float(_field(fields, "width", "linewidth"), 0.2),
                    layer=_layer_name(_field(fields, "layername", "layer") or "TopLayer"),
                )
                pcb.add_trace_segment(segment.net_name, segment)
                continue

            if record_type in {"via", "padvia"} or upper.startswith("VIA"):
                via = Via(
                    net_name=((_field(fields, "net", "netname") or "").strip().upper()),
                    x=_safe_float(_field(fields, "x", "locationx")),
                    y=_safe_float(_field(fields, "y", "locationy")),
                    drill=_safe_float(_field(fields, "holesize", "drill"), 0.3),
                    diameter=_safe_float(_field(fields, "size", "diameter"), 0.6),
                    layers=[layer for layer in list(pcb.layers)[:2] or ["TopLayer", "BottomLayer"]],
                )
                if via.net_name:
                    pcb.add_via(via.net_name, via)
                continue

            if record_type in {"arc", "trackarc"}:
                net_name = ((_field(fields, "net", "netname") or "").strip().upper()) or _layer_name(_field(fields, "layername", "layer")).upper()
                x1 = _safe_float(_field(fields, "x1", "xstart"))
                y1 = _safe_float(_field(fields, "y1", "ystart"))
                x2 = _safe_float(_field(fields, "x2", "xend"))
                y2 = _safe_float(_field(fields, "y2", "yend"))
                if any(value is None for value in [_field(fields, "x1", "xstart"), _field(fields, "y1", "ystart"), _field(fields, "x2", "xend"), _field(fields, "y2", "yend")]):
                    continue
                segment = TraceSegment(
                    net_name=net_name,
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                    width=_safe_float(_field(fields, "width", "linewidth"), 0.2),
                    layer=_layer_name(_field(fields, "layername", "layer") or "TopLayer"),
                )
                pcb.add_trace_segment(segment.net_name, segment)
                continue

            if record_type in {"fill", "region", "polygon"}:
                if fields.get("points"):
                    points = []
                    for token in fields.get("points", "").split(";"):
                        try:
                            x_text, y_text = token.split(",", 1)
                        except ValueError:
                            continue
                        points.append((_safe_float(x_text), _safe_float(y_text)))
                    if len(points) >= 3:
                        pcb.add_zone(
                            Zone(
                                net_name=((_field(fields, "net", "netname") or _layer_name(_field(fields, "layername", "layer"))).strip().upper()),
                                layer=_layer_name(_field(fields, "layername", "layer") or "TopLayer"),
                                points=points,
                            )
                        )
                        continue
                pending_region_points = []
                continue

            if record_type in {"vertex", "regionvertex", "polygonvertex"}:
                pending_region_points.append((_safe_float(fields.get("x")), _safe_float(fields.get("y"))))
                continue

            if record_type == "endregion":
                if len(pending_region_points) >= 3:
                    pcb.add_zone(
                        Zone(
                            net_name=((fields.get("net") or _layer_name(fields.get("layername") or fields.get("layer"))).strip().upper()),
                            layer=_layer_name(_field(fields, "layername", "layer") or "TopLayer"),
                            points=list(pending_region_points),
                        )
                    )
                pending_region_points = []
                continue

            if record_type in {"boardoutline", "outline", "edge", "boardline"}:
                if all(_field(fields, *keys) is not None for keys in (("x1", "xstart"), ("y1", "ystart"), ("x2", "xend"), ("y2", "yend"))):
                    pcb.add_outline_segment(
                        OutlineSegment(
                            x1=_safe_float(_field(fields, "x1", "xstart")),
                            y1=_safe_float(_field(fields, "y1", "ystart")),
                            x2=_safe_float(_field(fields, "x2", "xend")),
                            y2=_safe_float(_field(fields, "y2", "yend")),
                            layer="Edge.Cuts",
                            kind="line",
                        )
                    )
                continue

    if not pcb.layers:
        pcb.add_layers(["TopLayer", "BottomLayer"])
    pcb.estimate_board_bounds()
    return pcb
