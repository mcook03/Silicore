import re

from engine.pcb_model import PCB, OutlineSegment, TraceSegment


GERBER_COORD_RE = re.compile(r"X(-?\d+)Y(-?\d+)(D0[123])")


def _coord(value):
    try:
        return float(value) / 10000.0
    except (TypeError, ValueError):
        return 0.0


def parse_gerber_file(filepath):
    pcb = PCB(filename=filepath.split("/")[-1])
    pcb.source_format = "gerber"

    current_layer = "Gerber"
    current_point = None
    with open(filepath, "r", encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("%TF.FileFunction"):
                current_layer = line.replace("%TF.FileFunction,", "").replace("*%", "").strip() or current_layer
                pcb.add_layer(current_layer)
                continue
            if line.startswith("G04") and "layer" in line.lower():
                current_layer = line.replace("G04", "").replace("*", "").strip() or current_layer
                pcb.add_layer(current_layer)
                continue

            match = GERBER_COORD_RE.search(line)
            if not match:
                continue

            x = _coord(match.group(1))
            y = _coord(match.group(2))
            op = match.group(3)
            if op == "D02":
                current_point = (x, y)
                continue
            if current_point is None:
                current_point = (x, y)
                continue

            x1, y1 = current_point
            x2, y2 = x, y
            current_point = (x, y)

            if "outline" in current_layer.lower() or "edge" in current_layer.lower():
                pcb.add_outline_segment(OutlineSegment(x1=x1, y1=y1, x2=x2, y2=y2, layer=current_layer))
            else:
                pcb.add_trace_segment(
                    current_layer.upper(),
                    TraceSegment(
                        net_name=current_layer.upper(),
                        x1=x1,
                        y1=y1,
                        x2=x2,
                        y2=y2,
                        width=0.2,
                        layer=current_layer,
                    ),
                )

    pcb.estimate_board_bounds()
    return pcb
