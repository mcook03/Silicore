import math
import os
import re
import tempfile
import zipfile
from pathlib import Path

from engine.geometry_backend import flash_to_polygon, merge_polygons, simplify_path
from engine.pcb_model import OutlineSegment, PCB, TraceSegment, Via, Zone


try:  # pragma: no cover - optional dependency
    import gerbonara
except Exception:  # pragma: no cover - optional dependency
    gerbonara = None

try:  # pragma: no cover - optional dependency
    import gerber as pcb_tools_gerber
except Exception:  # pragma: no cover - optional dependency
    pcb_tools_gerber = None


GERBER_DRAW_RE = re.compile(r"^(?:G0[123])?(?:X(-?\d+))?(?:Y(-?\d+))?(?:I(-?\d+))?(?:J(-?\d+))?(?:D(\d+))?\*?$")
FORMAT_RE = re.compile(r"%FSL.AX(\d)(\d)Y(\d)(\d)\*%")
APERTURE_RE = re.compile(r"%ADD(\d+)([A-Z]),?(.+)?\*%")
FILE_FUNCTION_RE = re.compile(r"%TF\.FileFunction,([^*]+)\*%")
COMMENT_LAYER_RE = re.compile(r"G04\s+Layer[:\s]+(.+?)\*?$", re.IGNORECASE)
TOOL_RE = re.compile(r"^T(\d+)C?([0-9.\-]+)?")
EXCELLON_COORD_RE = re.compile(r"^(?:X(-?\d+))?(?:Y(-?\d+))?$")

GERBER_EXTENSIONS = {
    ".gbr",
    ".ger",
    ".gko",
    ".gtl",
    ".gbl",
    ".gto",
    ".gbo",
    ".gts",
    ".gbs",
    ".gm1",
    ".pho",
    ".art",
    ".outline",
}
DRILL_EXTENSIONS = {".drl", ".xln", ".txt"}


def parse_gerber_file(filepath):
    path = Path(filepath)
    if path.is_dir():
        return parse_gerber_directory(filepath)
    if path.suffix.lower() == ".zip":
        return parse_gerber_archive(filepath)
    if path.suffix.lower() in DRILL_EXTENSIONS:
        return parse_excellon_file(filepath)

    pcb = None
    for candidate in (_parse_with_gerbonara, _parse_with_pcb_tools, _parse_with_text_fallback):
        parsed = candidate(filepath)
        if parsed is None:
            continue
        if _pcb_has_geometry(parsed) or candidate is _parse_with_text_fallback:
            pcb = parsed
            break
    if pcb is None:
        pcb = _parse_with_text_fallback(filepath)
    pcb.estimate_board_bounds()
    return pcb


def parse_gerber_directory(directory):
    directory_path = Path(directory)
    pcb = PCB(filename=directory_path.name)
    pcb.source_format = "gerber_cam"

    cam_layers = []
    for path in sorted(directory_path.iterdir()):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix not in GERBER_EXTENSIONS and suffix not in DRILL_EXTENSIONS:
            continue
        child = parse_gerber_file(str(path))
        _merge_pcb(pcb, child)
        cam_layers.append(
            {
                "filename": path.name,
                "source_format": child.source_format,
                "layer_count": len(getattr(child, "layers", []) or []),
            }
        )

    pcb.merge_metadata(
        "cam",
        {
            "bundle_type": "directory",
            "layer_files": cam_layers,
            "layer_file_count": len(cam_layers),
        },
    )
    pcb.estimate_board_bounds()
    return pcb


def parse_gerber_archive(filepath):
    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(filepath, "r") as archive:
            archive.extractall(temp_dir)
        pcb = parse_gerber_directory(temp_dir)
        pcb.filename = Path(filepath).name
        pcb.merge_metadata("cam", {"bundle_type": "archive"})
        return pcb


def parse_excellon_file(filepath):
    pcb = PCB(filename=Path(filepath).name)
    pcb.source_format = "excellon_drill"
    pcb.merge_metadata("parser", {"backend": "text_fallback"})

    unit_scale = 1.0
    decimal_places = 4
    current_tool = {"diameter": 0.3}
    current_x = None
    current_y = None
    drill_hits = 0

    with open(filepath, "r", encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            line = raw_line.strip().upper()
            if not line:
                continue
            if "METRIC" in line:
                unit_scale = 1.0
                continue
            if "INCH" in line:
                unit_scale = 25.4
                continue
            if line.startswith("T"):
                tool_match = TOOL_RE.match(line)
                if tool_match:
                    if tool_match.group(2):
                        current_tool = {"diameter": float(tool_match.group(2)) * unit_scale}
                    continue
            if line.startswith("M72"):
                unit_scale = 25.4
                continue
            if line.startswith("M71"):
                unit_scale = 1.0
                continue

            coord_match = EXCELLON_COORD_RE.match(line)
            if not coord_match:
                continue
            if coord_match.group(1) is not None:
                current_x = _gerber_number_to_float(coord_match.group(1), decimal_places, unit_scale)
            if coord_match.group(2) is not None:
                current_y = _gerber_number_to_float(coord_match.group(2), decimal_places, unit_scale)
            if current_x is None or current_y is None:
                continue
            drill_hits += 1
            pcb.add_via(
                "DRILL",
                Via(
                    net_name="DRILL",
                    x=current_x,
                    y=current_y,
                    drill=current_tool.get("diameter", 0.3),
                    diameter=max(current_tool.get("diameter", 0.3) * 1.75, current_tool.get("diameter", 0.3)),
                    layers=["Drill"],
                ),
            )

    pcb.add_layer("Drill")
    pcb.merge_metadata("cam", {"drill_hits": drill_hits})
    return pcb


def _parse_with_gerbonara(filepath):  # pragma: no cover - optional dependency
    if gerbonara is None:
        return None

    try:
        document = None
        if hasattr(gerbonara, "GerberFile") and hasattr(gerbonara.GerberFile, "open"):
            document = gerbonara.GerberFile.open(filepath)
        elif hasattr(gerbonara, "load"):
            document = gerbonara.load(filepath)
        if document is None:
            return None
    except Exception:
        return None

    pcb = PCB(filename=Path(filepath).name)
    pcb.source_format = "gerber"
    pcb.merge_metadata("parser", {"backend": "gerbonara"})
    layer_name = _guess_layer_name(filepath, "")
    pcb.add_layer(layer_name)

    objects = getattr(document, "objects", None) or getattr(document, "primitives", None) or []
    flash_count = 0
    region_polygons = []
    for obj in objects:
        name = obj.__class__.__name__.lower()
        if "line" in name or "trace" in name:
            start = getattr(obj, "start", None)
            end = getattr(obj, "end", None)
            width = float(getattr(obj, "width", 0.2) or 0.2)
            if start and end:
                pcb.add_trace_segment(
                    layer_name.upper(),
                    TraceSegment(
                        net_name=layer_name.upper(),
                        x1=float(start[0]),
                        y1=float(start[1]),
                        x2=float(end[0]),
                        y2=float(end[1]),
                        width=width,
                        layer=layer_name,
                    ),
                )
        elif "arc" in name:
            points = _approximate_arc_from_object(obj)
            _add_polyline_as_traces(pcb, points, layer_name, float(getattr(obj, "width", 0.2) or 0.2))
        elif "flash" in name or "pad" in name:
            flash_count += 1
            position = getattr(obj, "position", None) or getattr(obj, "center", None)
            aperture = getattr(obj, "aperture", None)
            if position is not None:
                diameter = float(getattr(aperture, "diameter", 0.4) or getattr(obj, "diameter", 0.4) or 0.4)
                polygon = flash_to_polygon(float(position[0]), float(position[1]), diameter)
                pcb.add_zone(Zone(net_name=layer_name.upper(), layer=layer_name, points=polygon))
        elif "region" in name or "polygon" in name:
            points = _extract_points(obj)
            if len(points) >= 3:
                region_polygons.append(points)

    for polygon in merge_polygons(region_polygons):
        pcb.add_zone(Zone(net_name=layer_name.upper(), layer=layer_name, points=polygon))

    pcb.merge_metadata("cam", {"flash_count": flash_count, "region_count": len(region_polygons)})
    return pcb


def _parse_with_pcb_tools(filepath):  # pragma: no cover - optional dependency
    if pcb_tools_gerber is None:
        return None
    try:
        layer = pcb_tools_gerber.read(filepath)
    except Exception:
        return None

    pcb = PCB(filename=Path(filepath).name)
    pcb.source_format = "gerber"
    pcb.merge_metadata("parser", {"backend": "pcb_tools"})
    layer_name = _guess_layer_name(filepath, getattr(layer, "layer_name", ""))
    pcb.add_layer(layer_name)

    primitives = getattr(layer, "primitives", []) or []
    flashes = 0
    for primitive in primitives:
        name = primitive.__class__.__name__.lower()
        if "line" in name:
            start = getattr(primitive, "start", None)
            end = getattr(primitive, "end", None)
            width = float(getattr(primitive, "width", 0.2) or 0.2)
            if start and end:
                pcb.add_trace_segment(
                    layer_name.upper(),
                    TraceSegment(layer_name.upper(), start[0], start[1], end[0], end[1], width=width, layer=layer_name),
                )
        elif "arc" in name:
            points = _approximate_arc_from_object(primitive)
            _add_polyline_as_traces(pcb, points, layer_name, float(getattr(primitive, "width", 0.2) or 0.2))
        elif "region" in name or "polygon" in name:
            points = _extract_points(primitive)
            if len(points) >= 3:
                pcb.add_zone(Zone(net_name=layer_name.upper(), layer=layer_name, points=points))
        elif "drill" in name:
            pos = getattr(primitive, "position", None)
            diameter = float(getattr(primitive, "diameter", 0.3) or 0.3)
            if pos:
                pcb.add_via("DRILL", Via(net_name="DRILL", x=pos[0], y=pos[1], drill=diameter, diameter=diameter, layers=["Drill"]))
        elif "flash" in name:
            flashes += 1
            pos = getattr(primitive, "position", None)
            aperture = getattr(primitive, "aperture", None)
            diameter = float(getattr(aperture, "diameter", 0.4) or getattr(primitive, "diameter", 0.4) or 0.4)
            if pos:
                pcb.add_zone(Zone(net_name=layer_name.upper(), layer=layer_name, points=flash_to_polygon(pos[0], pos[1], diameter)))

    pcb.merge_metadata("cam", {"flash_count": flashes})
    return pcb


def _parse_with_text_fallback(filepath):
    pcb = PCB(filename=Path(filepath).name)
    pcb.source_format = "gerber"
    pcb.merge_metadata("parser", {"backend": "text_fallback"})

    state = {
        "units_scale": 1.0,
        "decimal_places": 4,
        "current_layer": _guess_layer_name(filepath, ""),
        "current_aperture": None,
        "apertures": {},
        "current_x": None,
        "current_y": None,
        "interpolation": "linear",
        "region_mode": False,
        "region_points": [],
        "flash_count": 0,
        "region_count": 0,
    }
    pcb.add_layer(state["current_layer"])

    with open(filepath, "r", encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("%MOMM"):
                state["units_scale"] = 1.0
                continue
            if line.startswith("%MOIN"):
                state["units_scale"] = 25.4
                continue

            format_match = FORMAT_RE.match(line)
            if format_match:
                state["decimal_places"] = int(format_match.group(2))
                continue

            file_function = FILE_FUNCTION_RE.match(line)
            if file_function:
                state["current_layer"] = _guess_layer_name(filepath, file_function.group(1))
                pcb.add_layer(state["current_layer"])
                continue

            layer_comment = COMMENT_LAYER_RE.match(line)
            if layer_comment:
                state["current_layer"] = _guess_layer_name(filepath, layer_comment.group(1))
                pcb.add_layer(state["current_layer"])
                continue

            aperture_match = APERTURE_RE.match(line)
            if aperture_match:
                state["apertures"][aperture_match.group(1)] = _parse_aperture(aperture_match)
                continue

            if line.startswith("G36"):
                state["region_mode"] = True
                state["region_points"] = []
                continue
            if line.startswith("G37"):
                _flush_region(pcb, state)
                continue
            if line.startswith("G02"):
                state["interpolation"] = "cw_arc"
                continue
            if line.startswith("G03"):
                state["interpolation"] = "ccw_arc"
                continue
            if line.startswith("G01"):
                state["interpolation"] = "linear"
                continue

            if line.startswith("D") and line[1:-1].isdigit() and int(line[1:-1]) >= 10:
                state["current_aperture"] = line[1:-1]
                continue

            draw_match = GERBER_DRAW_RE.match(line)
            if not draw_match:
                continue

            next_x = state["current_x"]
            next_y = state["current_y"]
            if draw_match.group(1) is not None:
                next_x = _gerber_number_to_float(draw_match.group(1), state["decimal_places"], state["units_scale"])
            if draw_match.group(2) is not None:
                next_y = _gerber_number_to_float(draw_match.group(2), state["decimal_places"], state["units_scale"])
            i_val = draw_match.group(3)
            j_val = draw_match.group(4)
            d_code = draw_match.group(5)

            if next_x is None or next_y is None:
                continue

            if d_code and int(d_code) >= 10:
                state["current_aperture"] = d_code
                d_code = None

            operation = str(int(d_code)) if d_code is not None else "1"
            if operation == "2":
                state["current_x"], state["current_y"] = next_x, next_y
                if state["region_mode"]:
                    state["region_points"].append((next_x, next_y))
                continue

            aperture = state["apertures"].get(str(state["current_aperture"] or ""))
            width = _aperture_width(aperture)
            current_point = (state["current_x"], state["current_y"])
            next_point = (next_x, next_y)

            if operation == "3":
                state["flash_count"] += 1
                polygon = flash_to_polygon(next_x, next_y, width, shape=(aperture or {}).get("shape", "circle"), size_x=(aperture or {}).get("size_x"), size_y=(aperture or {}).get("size_y"))
                pcb.add_zone(Zone(net_name=state["current_layer"].upper(), layer=state["current_layer"], points=polygon))
            elif current_point[0] is not None and current_point[1] is not None:
                if state["interpolation"] == "linear":
                    _add_trace_or_outline(pcb, state["current_layer"], current_point, next_point, width)
                    if state["region_mode"]:
                        state["region_points"].append(next_point)
                else:
                    points = _approximate_arc(current_point, next_point, i_val, j_val, state["decimal_places"], state["units_scale"], state["interpolation"] == "cw_arc")
                    if state["region_mode"]:
                        state["region_points"].extend(points[1:])
                    else:
                        _add_polyline_as_traces(pcb, points, state["current_layer"], width)

            state["current_x"], state["current_y"] = next_x, next_y

    _flush_region(pcb, state)
    pcb.merge_metadata(
        "cam",
        {
            "aperture_count": len(state["apertures"]),
            "flash_count": state["flash_count"],
            "region_count": state["region_count"],
        },
    )
    return pcb


def _merge_pcb(target, source):
    for layer in getattr(source, "declared_layers", []) or list(getattr(source, "layers", []) or []):
        target.add_layer(layer)
    for component in getattr(source, "components", []):
        target.add_component(component)
    for net_name, net in getattr(source, "nets", {}).items():
        for connection in getattr(net, "connections", []):
            target.add_net_connection(net_name, connection[0], connection[1])
        for segment in getattr(net, "trace_segments", []):
            target.add_trace_segment(net_name, segment)
        for via in getattr(net, "vias", []):
            target.add_via(net_name, via)
    for zone in getattr(source, "zones", []):
        target.add_zone(zone)
    for segment in getattr(source, "outline_segments", []):
        target.add_outline_segment(segment)

    source_cam = getattr(source, "metadata", {}).get("cam", {})
    target_cam = dict(target.metadata.get("cam", {}))
    if isinstance(source_cam, dict):
        target_cam.setdefault("merged_sources", []).append(
            {
                "filename": source.filename,
                "source_format": source.source_format,
                "trace_count": len(getattr(source, "traces", []) or []),
                "zone_count": len(getattr(source, "zones", []) or []),
            }
        )
    target.metadata["cam"] = target_cam


def _pcb_has_geometry(pcb):
    return any(
        len(getattr(pcb, attr, []) or []) > 0
        for attr in ("traces", "outline_segments", "zones", "vias")
    )


def _guess_layer_name(filepath, raw_value):
    raw = str(raw_value or "").strip()
    if raw:
        return raw.replace(",", " ").strip()
    suffix = Path(filepath).suffix.lower()
    mapping = {
        ".gko": "Edge.Cuts",
        ".gm1": "Edge.Cuts",
        ".gtl": "Top Copper",
        ".gbl": "Bottom Copper",
        ".gto": "Top Silkscreen",
        ".gbo": "Bottom Silkscreen",
        ".gts": "Top Soldermask",
        ".gbs": "Bottom Soldermask",
        ".drl": "Drill",
        ".xln": "Drill",
    }
    return mapping.get(suffix, "Gerber")


def _parse_aperture(match):
    code = match.group(1)
    shape = {"C": "circle", "R": "rect", "O": "obround", "P": "polygon"}.get(match.group(2), str(match.group(2)).lower())
    raw = (match.group(3) or "").split("X")
    values = [float(item) for item in raw if item and item.replace(".", "", 1).replace("-", "", 1).isdigit()]
    size_x = values[0] if values else 0.2
    size_y = values[1] if len(values) > 1 else size_x
    return {"code": code, "shape": shape, "size_x": size_x, "size_y": size_y, "diameter": max(size_x, size_y)}


def _aperture_width(aperture):
    if not aperture:
        return 0.2
    return max(float(aperture.get("diameter", 0.2) or 0.2), 0.01)


def _gerber_number_to_float(value, decimal_places, unit_scale):
    if value is None:
        return None
    sign = -1.0 if str(value).startswith("-") else 1.0
    digits = str(value).lstrip("+-")
    if not digits:
        return 0.0
    return sign * (int(digits) / (10 ** decimal_places)) * unit_scale


def _add_trace_or_outline(pcb, layer_name, start, end, width):
    if _is_outline_layer(layer_name):
        pcb.add_outline_segment(OutlineSegment(start[0], start[1], end[0], end[1], layer=layer_name, kind="line"))
    else:
        pcb.add_trace_segment(
            layer_name.upper(),
            TraceSegment(layer_name.upper(), start[0], start[1], end[0], end[1], width=width, layer=layer_name),
        )


def _add_polyline_as_traces(pcb, points, layer_name, width):
    cleaned = simplify_path(points, tolerance=0.001)
    for start, end in zip(cleaned, cleaned[1:]):
        _add_trace_or_outline(pcb, layer_name, start, end, width)


def _flush_region(pcb, state):
    if state["region_mode"] and len(state["region_points"]) >= 3:
        merged = merge_polygons([state["region_points"]])
        for polygon in merged:
            pcb.add_zone(Zone(net_name=state["current_layer"].upper(), layer=state["current_layer"], points=polygon))
        state["region_count"] += 1
    state["region_mode"] = False
    state["region_points"] = []


def _is_outline_layer(layer_name):
    lowered = str(layer_name or "").lower()
    return any(token in lowered for token in ["outline", "edge", "profile", "mechanical"])


def _approximate_arc(start, end, i_val, j_val, decimal_places, unit_scale, clockwise):
    if i_val is None or j_val is None:
        return [start, end]
    center_x = start[0] + _gerber_number_to_float(i_val, decimal_places, unit_scale)
    center_y = start[1] + _gerber_number_to_float(j_val, decimal_places, unit_scale)
    radius = math.dist(start, (center_x, center_y))
    if radius <= 0:
        return [start, end]

    start_angle = math.atan2(start[1] - center_y, start[0] - center_x)
    end_angle = math.atan2(end[1] - center_y, end[0] - center_x)
    if clockwise and end_angle >= start_angle:
        end_angle -= 2 * math.pi
    if not clockwise and end_angle <= start_angle:
        end_angle += 2 * math.pi

    steps = max(10, int(abs(end_angle - start_angle) / (math.pi / 18)))
    return [
        (center_x + radius * math.cos(angle), center_y + radius * math.sin(angle))
        for angle in [start_angle + ((end_angle - start_angle) * index / steps) for index in range(steps + 1)]
    ]


def _approximate_arc_from_object(obj):  # pragma: no cover - optional dependency
    start = getattr(obj, "start", None)
    end = getattr(obj, "end", None)
    center = getattr(obj, "center", None)
    clockwise = bool(getattr(obj, "clockwise", False))
    if not start or not end or not center:
        return []
    radius = math.dist((float(start[0]), float(start[1])), (float(center[0]), float(center[1])))
    start_angle = math.atan2(float(start[1]) - float(center[1]), float(start[0]) - float(center[0]))
    end_angle = math.atan2(float(end[1]) - float(center[1]), float(end[0]) - float(center[0]))
    if clockwise and end_angle >= start_angle:
        end_angle -= 2 * math.pi
    if not clockwise and end_angle <= start_angle:
        end_angle += 2 * math.pi
    steps = max(12, int(abs(end_angle - start_angle) / (math.pi / 18)))
    return [
        (
            float(center[0]) + radius * math.cos(start_angle + ((end_angle - start_angle) * index / steps)),
            float(center[1]) + radius * math.sin(start_angle + ((end_angle - start_angle) * index / steps)),
        )
        for index in range(steps + 1)
    ]


def _extract_points(obj):  # pragma: no cover - optional dependency
    for attr in ["outline", "points", "vertices", "coords"]:
        value = getattr(obj, attr, None)
        if value:
            points = []
            for point in value:
                if isinstance(point, (tuple, list)) and len(point) >= 2:
                    points.append((float(point[0]), float(point[1])))
                elif hasattr(point, "x") and hasattr(point, "y"):
                    points.append((float(point.x), float(point.y)))
            if points:
                return points
    return []
