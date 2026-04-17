import math


try:
    import numpy as _np
except Exception:  # pragma: no cover - optional dependency
    _np = None

try:
    from scipy.spatial import ConvexHull as _ConvexHull
except Exception:  # pragma: no cover - optional dependency
    _ConvexHull = None

try:
    from shapely.geometry import LineString as _ShapelyLineString
    from shapely.geometry import MultiPolygon as _ShapelyMultiPolygon
    from shapely.geometry import Point as _ShapelyPoint
    from shapely.geometry import Polygon as _ShapelyPolygon
    from shapely.ops import unary_union as _shapely_unary_union
except Exception:  # pragma: no cover - optional dependency
    _ShapelyLineString = None
    _ShapelyMultiPolygon = None
    _ShapelyPoint = None
    _ShapelyPolygon = None
    _shapely_unary_union = None

try:
    import pyclipper as _pyclipper
except Exception:  # pragma: no cover - optional dependency
    _pyclipper = None


LIBRARIES = {
    "numpy": _np is not None,
    "scipy": _ConvexHull is not None,
    "shapely": _ShapelyPolygon is not None,
    "pyclipper": _pyclipper is not None,
}


def get_geometry_capabilities():
    return dict(LIBRARIES)


def bounds(points):
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


def polygon_area(points):
    if not points or len(points) < 3:
        return 0.0
    if _ShapelyPolygon is not None:
        try:
            return float(abs(_ShapelyPolygon(points).area))
        except Exception:
            pass
    if _np is not None:
        try:
            arr = _np.array(points, dtype=float)
            x = arr[:, 0]
            y = arr[:, 1]
            return float(abs(_np.dot(x, _np.roll(y, -1)) - _np.dot(y, _np.roll(x, -1))) / 2.0)
        except Exception:
            pass
    area = 0.0
    for index, point in enumerate(points):
        next_point = points[(index + 1) % len(points)]
        area += (point[0] * next_point[1]) - (next_point[0] * point[1])
    return abs(area) / 2.0


def line_length(points):
    if not points or len(points) < 2:
        return 0.0
    if _ShapelyLineString is not None:
        try:
            return float(_ShapelyLineString(points).length)
        except Exception:
            pass
    length = 0.0
    for start, end in zip(points, points[1:]):
        length += math.dist(start, end)
    return length


def simplify_path(points, tolerance=0.02):
    if not points or len(points) < 3:
        return list(points or [])
    if _ShapelyLineString is not None:
        try:
            line = _ShapelyLineString(points).simplify(tolerance, preserve_topology=False)
            return [(float(x), float(y)) for x, y in line.coords]
        except Exception:
            pass
    return _rdp(points, tolerance)


def convex_hull(points):
    if not points:
        return []
    if len(points) <= 3:
        return list(points)
    if _ConvexHull is not None and _np is not None:
        try:
            arr = _np.array(points, dtype=float)
            hull = _ConvexHull(arr)
            return [(float(arr[i][0]), float(arr[i][1])) for i in hull.vertices]
        except Exception:
            pass
    return _monotonic_hull(points)


def merge_polygons(polygons):
    clean = [list(polygon) for polygon in polygons if polygon and len(polygon) >= 3]
    if not clean:
        return []
    if _ShapelyPolygon is not None and _shapely_unary_union is not None:
        try:
            merged = _shapely_unary_union([_ShapelyPolygon(poly) for poly in clean])
            if isinstance(merged, _ShapelyMultiPolygon):
                return [
                    [(float(x), float(y)) for x, y in poly.exterior.coords[:-1]]
                    for poly in merged.geoms
                ]
            return [[(float(x), float(y)) for x, y in merged.exterior.coords[:-1]]]
        except Exception:
            pass
    return clean


def offset_polygon(points, distance):
    if not points or len(points) < 3:
        return []
    if _ShapelyPolygon is not None:
        try:
            buffered = _ShapelyPolygon(points).buffer(distance)
            if buffered.is_empty:
                return []
            if isinstance(buffered, _ShapelyMultiPolygon):
                buffered = max(buffered.geoms, key=lambda item: item.area)
            return [(float(x), float(y)) for x, y in buffered.exterior.coords[:-1]]
        except Exception:
            pass
    if _pyclipper is not None:
        try:
            scale = 1000.0
            offset = _pyclipper.PyclipperOffset()
            offset.AddPath(
                [(int(point[0] * scale), int(point[1] * scale)) for point in points],
                _pyclipper.JT_ROUND,
                _pyclipper.ET_CLOSEDPOLYGON,
            )
            solution = offset.Execute(distance * scale)
            if solution:
                return [(item[0] / scale, item[1] / scale) for item in solution[0]]
        except Exception:
            pass
    return list(points)


def flash_to_polygon(x, y, diameter, shape="circle", size_x=None, size_y=None):
    radius = max(float(diameter or 0.0) / 2.0, 0.001)
    shape = str(shape or "circle").lower()
    if _ShapelyPoint is not None and shape == "circle":
        try:
            region = _ShapelyPoint(float(x), float(y)).buffer(radius, quad_segs=24)
            return [(float(px), float(py)) for px, py in region.exterior.coords[:-1]]
        except Exception:
            pass
    if shape == "rect":
        half_x = max(float(size_x or diameter or 0.0) / 2.0, radius)
        half_y = max(float(size_y or diameter or 0.0) / 2.0, radius)
        return [
            (x - half_x, y - half_y),
            (x + half_x, y - half_y),
            (x + half_x, y + half_y),
            (x - half_x, y + half_y),
        ]
    segments = 20
    return [
        (
            float(x) + radius * math.cos((2.0 * math.pi * index) / segments),
            float(y) + radius * math.sin((2.0 * math.pi * index) / segments),
        )
        for index in range(segments)
    ]


def polygon_distance(poly_a, poly_b):
    if not poly_a or not poly_b:
        return None
    if _ShapelyPolygon is not None:
        try:
            return float(_ShapelyPolygon(poly_a).distance(_ShapelyPolygon(poly_b)))
        except Exception:
            pass
    return _fallback_polygon_distance(poly_a, poly_b)


def line_distance_to_polygon(line_points, polygon_points, width=0.0):
    if not line_points or not polygon_points or len(line_points) < 2:
        return None
    if _ShapelyLineString is not None and _ShapelyPolygon is not None:
        try:
            line = _ShapelyLineString(line_points)
            if width > 0:
                line = line.buffer(width / 2.0)
            region = _ShapelyPolygon(polygon_points)
            return float(line.distance(region))
        except Exception:
            pass
    return _fallback_polygon_distance(_buffer_line_to_polygon(line_points, width), polygon_points)


def polygon_intersection_area(poly_a, poly_b):
    if not poly_a or not poly_b:
        return 0.0
    if _ShapelyPolygon is not None:
        try:
            return float(_ShapelyPolygon(poly_a).intersection(_ShapelyPolygon(poly_b)).area)
        except Exception:
            pass
    return 0.0


def line_to_polygon(points, width=0.0):
    return _buffer_line_to_polygon(points, width)


def _rdp(points, epsilon):
    if len(points) < 3:
        return list(points)
    start = points[0]
    end = points[-1]
    max_distance = -1.0
    max_index = 0
    for index in range(1, len(points) - 1):
        distance = _point_line_distance(points[index], start, end)
        if distance > max_distance:
            max_distance = distance
            max_index = index
    if max_distance > epsilon:
        left = _rdp(points[: max_index + 1], epsilon)
        right = _rdp(points[max_index:], epsilon)
        return left[:-1] + right
    return [start, end]


def _point_line_distance(point, start, end):
    if start == end:
        return math.dist(point, start)
    x0, y0 = point
    x1, y1 = start
    x2, y2 = end
    numerator = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
    denominator = math.hypot(y2 - y1, x2 - x1)
    return numerator / denominator if denominator else 0.0


def _monotonic_hull(points):
    sorted_points = sorted(set((float(x), float(y)) for x, y in points))
    if len(sorted_points) <= 1:
        return sorted_points

    def cross(origin, a, b):
        return (a[0] - origin[0]) * (b[1] - origin[1]) - (a[1] - origin[1]) * (b[0] - origin[0])

    lower = []
    for point in sorted_points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)

    upper = []
    for point in reversed(sorted_points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)

    return lower[:-1] + upper[:-1]


def _buffer_line_to_polygon(points, width):
    if not points:
        return []
    width = max(float(width or 0.0), 0.001)
    if _ShapelyLineString is not None:
        try:
            region = _ShapelyLineString(points).buffer(width / 2.0, cap_style=1, join_style=1)
            if region.is_empty:
                return []
            if isinstance(region, _ShapelyMultiPolygon):
                region = max(region.geoms, key=lambda item: item.area)
            return [(float(x), float(y)) for x, y in region.exterior.coords[:-1]]
        except Exception:
            pass
    start = points[0]
    end = points[-1]
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy) or 1.0
    nx = -(dy / length) * (width / 2.0)
    ny = (dx / length) * (width / 2.0)
    return [
        (start[0] + nx, start[1] + ny),
        (end[0] + nx, end[1] + ny),
        (end[0] - nx, end[1] - ny),
        (start[0] - nx, start[1] - ny),
    ]


def _fallback_polygon_distance(poly_a, poly_b):
    min_distance = None
    for point in poly_a:
        for other in poly_b:
            distance = math.dist(point, other)
            if min_distance is None or distance < min_distance:
                min_distance = distance
    return min_distance
