from engine.geometry_backend import bounds, line_length, polygon_area


def segment_length(x1, y1, x2, y2):
    return line_length([(float(x1), float(y1)), (float(x2), float(y2))])


def bounding_box(points):
    return bounds(points)


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


def zone_area(zone):
    return polygon_area(getattr(zone, "points", []))
