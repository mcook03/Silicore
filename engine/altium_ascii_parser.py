import re

from engine.pcb_model import PCB, Component, OutlineSegment, Pad, TraceSegment, Via, Zone


def _safe_float(value, default=0.0):
    try:
        return float(value)
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
                ref_text = fields.get("designator") or f"U{len(component_map) + 1}"
                component = Component(
                    ref=ref_text,
                    value=fields.get("comment") or fields.get("value") or ref_text,
                    x=_safe_float(fields.get("x")),
                    y=_safe_float(fields.get("y")),
                    layer=_layer_name(fields.get("layername") or fields.get("layer") or "TopLayer"),
                    comp_type="ic",
                )
                pcb.add_component(component)
                component_map[component.ref] = component
                current_component = component
                continue

            if record_type == "pad" or upper.startswith("PAD"):
                component_ref = fields.get("component") or fields.get("componentref") or (current_component.ref if current_component else "UNKNOWN")
                component = component_map.get(component_ref)
                if component is None:
                    component = Component(
                        ref=component_ref,
                        value=component_ref,
                        x=_safe_float(fields.get("x")),
                        y=_safe_float(fields.get("y")),
                        layer=_layer_name(fields.get("layername") or fields.get("layer") or "TopLayer"),
                        comp_type="unknown",
                    )
                    pcb.add_component(component)
                    component_map[component_ref] = component
                pad = Pad(
                    component_ref=component_ref,
                    pad_name=fields.get("name") or fields.get("pad") or "1",
                    net_name=((fields.get("net") or "").strip().upper()),
                    x=_safe_float(fields.get("x")) if fields.get("x") is not None else component.x,
                    y=_safe_float(fields.get("y")) if fields.get("y") is not None else component.y,
                    layer=_layer_name(fields.get("layername") or fields.get("layer") or component.layer),
                    size_x=_safe_float(fields.get("sizex") or fields.get("size") or fields.get("xsize")),
                    size_y=_safe_float(fields.get("sizey") or fields.get("size") or fields.get("ysize")),
                )
                component.add_pad(pad)
                if pad.net_name:
                    pcb.add_net_connection(pad.net_name, pad.component_ref, pad.pad_name)
                continue

            if record_type == "track" or upper.startswith("TRACK"):
                if not all(fields.get(key) is not None for key in ("net", "x1", "y1", "x2", "y2")):
                    continue
                segment = TraceSegment(
                    net_name=fields.get("net", "").strip().upper(),
                    x1=_safe_float(fields.get("x1")),
                    y1=_safe_float(fields.get("y1")),
                    x2=_safe_float(fields.get("x2")),
                    y2=_safe_float(fields.get("y2")),
                    width=_safe_float(fields.get("width"), 0.2),
                    layer=_layer_name(fields.get("layername") or fields.get("layer") or "TopLayer"),
                )
                pcb.add_trace_segment(segment.net_name, segment)
                continue

            if record_type == "via" or upper.startswith("VIA"):
                via = Via(
                    net_name=((fields.get("net") or "").strip().upper()),
                    x=_safe_float(fields.get("x")),
                    y=_safe_float(fields.get("y")),
                    drill=_safe_float(fields.get("holesize"), 0.3),
                    diameter=_safe_float(fields.get("size"), 0.6),
                    layers=[layer for layer in list(pcb.layers)[:2] or ["TopLayer", "BottomLayer"]],
                )
                if via.net_name:
                    pcb.add_via(via.net_name, via)
                continue

            if record_type == "arc":
                net_name = (fields.get("net") or "").strip().upper() or _layer_name(fields.get("layername") or fields.get("layer")).upper()
                x1 = _safe_float(fields.get("x1") or fields.get("xstart"))
                y1 = _safe_float(fields.get("y1") or fields.get("ystart"))
                x2 = _safe_float(fields.get("x2") or fields.get("xend"))
                y2 = _safe_float(fields.get("y2") or fields.get("yend"))
                if any(value is None for value in [fields.get("x1") or fields.get("xstart"), fields.get("y1") or fields.get("ystart"), fields.get("x2") or fields.get("xend"), fields.get("y2") or fields.get("yend")]):
                    continue
                segment = TraceSegment(
                    net_name=net_name,
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                    width=_safe_float(fields.get("width"), 0.2),
                    layer=_layer_name(fields.get("layername") or fields.get("layer") or "TopLayer"),
                )
                pcb.add_trace_segment(segment.net_name, segment)
                continue

            if record_type in {"fill", "region"}:
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
                                net_name=((fields.get("net") or _layer_name(fields.get("layername") or fields.get("layer"))).strip().upper()),
                                layer=_layer_name(fields.get("layername") or fields.get("layer") or "TopLayer"),
                                points=points,
                            )
                        )
                        continue
                pending_region_points = []
                continue

            if record_type == "vertex":
                pending_region_points.append((_safe_float(fields.get("x")), _safe_float(fields.get("y"))))
                continue

            if record_type == "endregion":
                if len(pending_region_points) >= 3:
                    pcb.add_zone(
                        Zone(
                            net_name=((fields.get("net") or _layer_name(fields.get("layername") or fields.get("layer"))).strip().upper()),
                            layer=_layer_name(fields.get("layername") or fields.get("layer") or "TopLayer"),
                            points=list(pending_region_points),
                        )
                    )
                pending_region_points = []
                continue

            if record_type in {"boardoutline", "outline", "edge"}:
                if all(fields.get(key) is not None for key in ("x1", "y1", "x2", "y2")):
                    pcb.add_outline_segment(
                        OutlineSegment(
                            x1=_safe_float(fields.get("x1")),
                            y1=_safe_float(fields.get("y1")),
                            x2=_safe_float(fields.get("x2")),
                            y2=_safe_float(fields.get("y2")),
                            layer="Edge.Cuts",
                            kind="line",
                        )
                    )
                continue

    if not pcb.layers:
        pcb.add_layers(["TopLayer", "BottomLayer"])
    pcb.estimate_board_bounds()
    return pcb
