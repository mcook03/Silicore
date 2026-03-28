def segment_length(x1, y1, x2, y2):
    dx = float(x2) - float(x1)
    dy = float(y2) - float(y1)
    return (dx ** 2 + dy ** 2) ** 0.5


def bounding_box(points):
    if not points:
        return None

    xs = [point[0] for point in points]
    ys = [point[1] for point in points]

    return {
        "min_x": min(xs),
        "max_x": max(xs),
        "min_y": min(ys),
        "max_y": max(ys),
        "width": max(xs) - min(xs),
        "height": max(ys) - min(ys),
    }


def net_bounding_box(net):
    points = []

    for segment in getattr(net, "trace_segments", []):
        points.append((segment.x1, segment.y1))
        points.append((segment.x2, segment.y2))

    for via in getattr(net, "vias", []):
        points.append((via.x, via.y))

    return bounding_box(points)


def average_trace_width(net):
    segments = getattr(net, "trace_segments", [])
    if not segments:
        return None

    widths = [segment.width for segment in segments if segment.width is not None]
    if not widths:
        return None

    return sum(widths) / len(widths)


def total_via_transitions(net):
    return len(getattr(net, "vias", []))