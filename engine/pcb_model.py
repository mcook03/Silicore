from engine.geometry_backend import get_geometry_capabilities, polygon_area


class Pad:
    def __init__(
        self,
        component_ref="",
        pad_name="",
        net_name=None,
        x=0.0,
        y=0.0,
        layer=None,
        size_x=0.0,
        size_y=0.0,
    ):
        self.component_ref = component_ref
        self.pad_name = str(pad_name)
        self.pad_number = str(pad_name)
        self.net_name = net_name
        self.x = float(x)
        self.y = float(y)
        self.layer = layer
        self.size_x = float(size_x)
        self.size_y = float(size_y)

    def to_dict(self):
        return {
            "component_ref": self.component_ref,
            "pad_name": self.pad_name,
            "pad_number": self.pad_number,
            "net_name": self.net_name,
            "x": self.x,
            "y": self.y,
            "layer": self.layer,
            "size_x": self.size_x,
            "size_y": self.size_y,
        }


class TraceSegment:
    def __init__(self, net_name, x1, y1, x2, y2, width=0.0, layer=None):
        self.net_name = net_name
        self.x1 = float(x1)
        self.y1 = float(y1)
        self.x2 = float(x2)
        self.y2 = float(y2)
        self.width = float(width)
        self.layer = layer

    @property
    def length(self):
        dx = self.x2 - self.x1
        dy = self.y2 - self.y1
        return (dx ** 2 + dy ** 2) ** 0.5

    def to_dict(self):
        return {
            "net_name": self.net_name,
            "x1": self.x1,
            "y1": self.y1,
            "x2": self.x2,
            "y2": self.y2,
            "width": self.width,
            "layer": self.layer,
            "length": round(self.length, 4),
        }


class Trace(TraceSegment):
    pass


class Via:
    def __init__(self, net_name="", x=0.0, y=0.0, drill=0.0, diameter=0.0, layers=None):
        self.net_name = net_name
        self.x = float(x)
        self.y = float(y)
        self.drill = float(drill)
        self.diameter = float(diameter)
        self.layers = layers or []

    def to_dict(self):
        return {
            "net_name": self.net_name,
            "x": self.x,
            "y": self.y,
            "drill": self.drill,
            "diameter": self.diameter,
            "layers": self.layers,
        }


class Zone:
    def __init__(self, net_name="", layer="", points=None):
        self.net_name = net_name
        self.layer = layer
        self.points = points or []

    @property
    def area_estimate(self):
        return polygon_area(self.points)

    def to_dict(self):
        return {
            "net_name": self.net_name,
            "layer": self.layer,
            "points": [{"x": point[0], "y": point[1]} for point in self.points],
            "area_estimate": round(self.area_estimate, 4),
        }


class OutlineSegment:
    def __init__(self, x1=0.0, y1=0.0, x2=0.0, y2=0.0, layer="Edge.Cuts", kind="line"):
        self.x1 = float(x1)
        self.y1 = float(y1)
        self.x2 = float(x2)
        self.y2 = float(y2)
        self.layer = layer
        self.kind = kind

    @property
    def length(self):
        dx = self.x2 - self.x1
        dy = self.y2 - self.y1
        return (dx ** 2 + dy ** 2) ** 0.5

    def to_dict(self):
        return {
            "x1": self.x1,
            "y1": self.y1,
            "x2": self.x2,
            "y2": self.y2,
            "layer": self.layer,
            "kind": self.kind,
            "length": round(self.length, 4),
        }


class Component:
    def __init__(
        self,
        ref,
        value,
        x,
        y,
        layer="F.Cu",
        comp_type="unknown",
        footprint="",
        rotation=0.0,
    ):
        self.ref = ref
        self.value = value
        self.x = float(x)
        self.y = float(y)
        self.layer = layer
        self.type = comp_type
        self.footprint = footprint
        self.rotation = float(rotation)
        self.pads = []

        # legacy compatibility fields
        self.net_name = ""
        self.net_names = []
        self.connected_nets = []

    def add_pad(self, pad):
        self.pads.append(pad)
        self.sync_nets_from_pads()

    def sync_nets_from_pads(self):
        nets = []
        for pad in self.pads:
            net_name = getattr(pad, "net_name", None)
            if net_name and net_name not in nets:
                nets.append(net_name)

        self.net_names = list(nets)
        self.connected_nets = list(nets)
        self.net_name = nets[0] if nets else ""

    def get_nets(self):
        self.sync_nets_from_pads()
        return list(self.net_names)

    @property
    def net(self):
        self.sync_nets_from_pads()
        return self.net_name if self.net_name else None

    def to_dict(self):
        self.sync_nets_from_pads()
        return {
            "ref": self.ref,
            "value": self.value,
            "x": self.x,
            "y": self.y,
            "layer": self.layer,
            "type": self.type,
            "footprint": self.footprint,
            "rotation": self.rotation,
            "net_name": self.net_name,
            "net_names": self.net_names,
            "connected_nets": self.connected_nets,
            "pads": [pad.to_dict() for pad in self.pads],
        }


class Net:
    def __init__(self, name):
        self.name = name
        self.connections = []
        self.trace_segments = []
        self.vias = []

    def add_connection(self, component_ref, pad_name):
        entry = (component_ref, str(pad_name))
        if entry not in self.connections:
            self.connections.append(entry)

    def add_trace_segment(self, segment):
        self.trace_segments.append(segment)

    def add_via(self, via):
        self.vias.append(via)

    @property
    def total_trace_length(self):
        return sum(segment.length for segment in self.trace_segments)

    @property
    def min_trace_width(self):
        widths = [
            segment.width
            for segment in self.trace_segments
            if getattr(segment, "width", None) is not None
        ]
        if not widths:
            return None
        return min(widths)

    @property
    def max_trace_width(self):
        widths = [
            segment.width
            for segment in self.trace_segments
            if getattr(segment, "width", None) is not None
        ]
        if not widths:
            return None
        return max(widths)

    @property
    def via_count(self):
        return len(self.vias)

    @property
    def layer_count(self):
        layers = set()

        for segment in self.trace_segments:
            if getattr(segment, "layer", None):
                layers.add(segment.layer)

        for via in self.vias:
            for layer in getattr(via, "layers", []):
                if layer:
                    layers.add(layer)

        return len(layers)

    def to_dict(self):
        return {
            "name": self.name,
            "connections": self.connections,
            "trace_segments": [segment.to_dict() for segment in self.trace_segments],
            "vias": [via.to_dict() for via in self.vias],
            "total_trace_length": round(self.total_trace_length, 4),
            "min_trace_width": self.min_trace_width,
            "max_trace_width": self.max_trace_width,
            "via_count": self.via_count,
            "layer_count": self.layer_count,
        }


class PCB:
    def __init__(self, filename="unknown"):
        self.filename = filename
        self.components = []
        self.nets = {}
        self.layers = set()
        self.declared_layers = []
        self.board_bounds = None
        self.board_width = 0.0
        self.board_height = 0.0
        self.source_format = "unknown"
        self.metadata = {
            "geometry_capabilities": get_geometry_capabilities(),
            "parser": {},
            "cam": {},
        }

        # legacy compatibility collections
        self.traces = []
        self.vias = []
        self.zones = []
        self.outline_segments = []

    def add_layer(self, layer_name):
        if layer_name:
            self.layers.add(layer_name)
            if layer_name not in self.declared_layers:
                self.declared_layers.append(layer_name)

    def add_layers(self, layer_names):
        for layer_name in layer_names:
            self.add_layer(layer_name)

    def add_component(self, component):
        component.sync_nets_from_pads()
        self.components.append(component)
        self.add_layer(getattr(component, "layer", None))

        for pad in getattr(component, "pads", []):
            pad_layer = getattr(pad, "layer", None)
            if isinstance(pad_layer, str) and "," in pad_layer:
                self.add_layers([item.strip() for item in pad_layer.split(",") if item.strip()])
            else:
                self.add_layer(pad_layer)

    def get_component(self, ref):
        for component in self.components:
            if component.ref == ref:
                return component
        return None

    def ensure_net(self, net_name):
        if net_name not in self.nets:
            self.nets[net_name] = Net(net_name)
        return self.nets[net_name]

    def add_net_connection(self, net_name, component_ref, pad_name):
        net = self.ensure_net(net_name)
        net.add_connection(component_ref, pad_name)

        component = self.get_component(component_ref)
        if component is not None:
            component.sync_nets_from_pads()

    def add_trace_segment(self, net_name, segment):
        net = self.ensure_net(net_name)
        net.add_trace_segment(segment)
        self.traces.append(segment)
        self.add_layer(getattr(segment, "layer", None))

    def add_trace(self, trace):
        self.add_trace_segment(trace.net_name, trace)

    def add_via(self, net_name, via):
        net = self.ensure_net(net_name)
        net.add_via(via)
        self.vias.append(via)
        self.add_layers(getattr(via, "layers", []))

    def add_zone(self, zone):
        self.zones.append(zone)
        self.add_layer(getattr(zone, "layer", None))

    def add_outline_segment(self, segment):
        self.outline_segments.append(segment)
        self.add_layer(getattr(segment, "layer", None))

    def get_traces_by_net(self, net_name):
        net = self.nets.get(net_name)
        if not net:
            return []
        return net.trace_segments

    def get_vias_by_net(self, net_name):
        net = self.nets.get(net_name)
        if not net:
            return []
        return net.vias

    def total_trace_length_for_net(self, net_name):
        net = self.nets.get(net_name)
        if not net:
            return 0.0
        return net.total_trace_length

    def min_trace_width_for_net(self, net_name):
        net = self.nets.get(net_name)
        if not net:
            return None
        return net.min_trace_width

    def max_trace_width_for_net(self, net_name):
        net = self.nets.get(net_name)
        if not net:
            return None
        return net.max_trace_width

    def via_count_for_net(self, net_name):
        net = self.nets.get(net_name)
        if not net:
            return 0
        return net.via_count

    def layer_count_for_net(self, net_name):
        net = self.nets.get(net_name)
        if not net:
            return 0
        return net.layer_count

    def estimate_board_bounds(self):
        points = []

        for component in self.components:
            points.append((component.x, component.y))

            for pad in getattr(component, "pads", []):
                points.append((pad.x, pad.y))

        for net in self.nets.values():
            for segment in getattr(net, "trace_segments", []):
                points.append((segment.x1, segment.y1))
                points.append((segment.x2, segment.y2))

            for via in getattr(net, "vias", []):
                points.append((via.x, via.y))

        for trace in self.traces:
            points.append((trace.x1, trace.y1))
            points.append((trace.x2, trace.y2))

        for via in self.vias:
            points.append((via.x, via.y))

        for segment in self.outline_segments:
            points.append((segment.x1, segment.y1))
            points.append((segment.x2, segment.y2))

        for zone in self.zones:
            for point in getattr(zone, "points", []):
                points.append((point[0], point[1]))

        if not points:
            self.board_bounds = {
                "min_x": 0.0,
                "max_x": 0.0,
                "min_y": 0.0,
                "max_y": 0.0,
                "width": 0.0,
                "height": 0.0,
            }
            self.board_width = 0.0
            self.board_height = 0.0
            return self.board_bounds

        xs = [point[0] for point in points]
        ys = [point[1] for point in points]

        self.board_bounds = {
            "min_x": min(xs),
            "max_x": max(xs),
            "min_y": min(ys),
            "max_y": max(ys),
            "width": max(xs) - min(xs),
            "height": max(ys) - min(ys),
        }
        self.board_width = self.board_bounds["width"]
        self.board_height = self.board_bounds["height"]
        return self.board_bounds

    def set_metadata(self, key, value):
        self.metadata[key] = value

    def merge_metadata(self, key, value):
        current = self.metadata.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            current.update(value)
            self.metadata[key] = current
        elif isinstance(current, list) and isinstance(value, list):
            self.metadata[key] = current + value
        else:
            self.metadata[key] = value

    def to_dict(self):
        return {
            "filename": self.filename,
            "declared_layers": list(self.declared_layers),
            "layers": sorted(list(self.layers)),
            "board_bounds": self.board_bounds,
            "board_width": self.board_width,
            "board_height": self.board_height,
            "source_format": self.source_format,
            "metadata": self.metadata,
            "components": [component.to_dict() for component in self.components],
            "nets": {name: net.to_dict() for name, net in self.nets.items()},
            "traces": [trace.to_dict() for trace in self.traces],
            "vias": [via.to_dict() for via in self.vias],
            "zones": [zone.to_dict() for zone in self.zones],
            "outline_segments": [segment.to_dict() for segment in self.outline_segments],
        }
