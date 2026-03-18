class Component:
    def __init__(self, ref, value, x, y, layer, comp_type, footprint="", rotation=0.0):
        self.ref = ref
        self.value = value
        self.x = float(x)
        self.y = float(y)
        self.layer = layer
        self.type = comp_type
        self.footprint = footprint
        self.rotation = float(rotation)
        self.pads = []

    def to_dict(self):
        return {
            "ref": self.ref,
            "value": self.value,
            "x": self.x,
            "y": self.y,
            "layer": self.layer,
            "type": self.type,
            "footprint": self.footprint,
            "rotation": self.rotation,
            "pads": [pad.to_dict() for pad in self.pads],
        }


class Pad:
    def __init__(self, pad_number, x, y, net_name="", layer="", size_x=0.0, size_y=0.0):
        self.pad_number = str(pad_number)
        self.x = float(x)
        self.y = float(y)
        self.net_name = net_name
        self.layer = layer
        self.size_x = float(size_x)
        self.size_y = float(size_y)

    def to_dict(self):
        return {
            "pad_number": self.pad_number,
            "x": self.x,
            "y": self.y,
            "net_name": self.net_name,
            "layer": self.layer,
            "size_x": self.size_x,
            "size_y": self.size_y,
        }


class Net:
    def __init__(self, name):
        self.name = name
        self.connections = []

    def to_dict(self):
        return {
            "name": self.name,
            "connections": self.connections,
        }


class Trace:
    def __init__(self, net_name, x1, y1, x2, y2, layer="", width=0.0):
        self.net_name = net_name
        self.x1 = float(x1)
        self.y1 = float(y1)
        self.x2 = float(x2)
        self.y2 = float(y2)
        self.layer = layer
        self.width = float(width)

    def length(self):
        dx = self.x2 - self.x1
        dy = self.y2 - self.y1
        return (dx ** 2 + dy ** 2) ** 0.5

    def midpoint(self):
        return ((self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0)

    def to_dict(self):
        return {
            "net_name": self.net_name,
            "x1": self.x1,
            "y1": self.y1,
            "x2": self.x2,
            "y2": self.y2,
            "layer": self.layer,
            "width": self.width,
            "length": round(self.length(), 2),
        }


class Via:
    def __init__(self, x, y, drill=0.0, net_name="", diameter=0.0):
        self.x = float(x)
        self.y = float(y)
        self.drill = float(drill)
        self.net_name = net_name
        self.diameter = float(diameter)

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "drill": self.drill,
            "net_name": self.net_name,
            "diameter": self.diameter,
        }


class Zone:
    def __init__(self, net_name="", layer=""):
        self.net_name = net_name
        self.layer = layer

    def to_dict(self):
        return {
            "net_name": self.net_name,
            "layer": self.layer,
        }


class PCB:
    def __init__(self):
        self.components = []
        self.nets = {}
        self.traces = []
        self.vias = []
        self.zones = []
        self.layers = set()
        self.board_width = 0.0
        self.board_height = 0.0
        self.source_format = "unknown"

    def add_component(self, component):
        self.components.append(component)
        if component.layer:
            self.layers.add(component.layer)

    def add_trace(self, trace):
        self.traces.append(trace)
        if trace.layer:
            self.layers.add(trace.layer)

    def add_via(self, via):
        self.vias.append(via)

    def add_zone(self, zone):
        self.zones.append(zone)
        if zone.layer:
            self.layers.add(zone.layer)

    def add_net_connection(self, net_name, ref, pin):
        if net_name not in self.nets:
            self.nets[net_name] = Net(net_name)
        self.nets[net_name].connections.append((ref, pin))

    def get_component(self, ref):
        for component in self.components:
            if component.ref == ref:
                return component
        return None

    def get_traces_by_net(self, net_name):
        return [trace for trace in self.traces if trace.net_name.upper() == net_name.upper()]

    def get_vias_by_net(self, net_name):
        return [via for via in self.vias if via.net_name.upper() == net_name.upper()]

    def get_zones_by_net(self, net_name):
        return [zone for zone in self.zones if zone.net_name.upper() == net_name.upper()]

    def total_trace_length_for_net(self, net_name):
        return round(sum(trace.length() for trace in self.get_traces_by_net(net_name)), 2)

    def min_trace_width_for_net(self, net_name):
        traces = self.get_traces_by_net(net_name)
        if not traces:
            return None
        return min(trace.width for trace in traces)

    def estimate_board_bounds(self):
        xs = [c.x for c in self.components]
        ys = [c.y for c in self.components]

        trace_xs = []
        trace_ys = []
        for t in self.traces:
            trace_xs.extend([t.x1, t.x2])
            trace_ys.extend([t.y1, t.y2])

        all_xs = xs + trace_xs
        all_ys = ys + trace_ys

        if all_xs and all_ys:
            self.board_width = max(all_xs) - min(all_xs)
            self.board_height = max(all_ys) - min(all_ys)

    def to_dict(self):
        return {
            "source_format": self.source_format,
            "board_width": self.board_width,
            "board_height": self.board_height,
            "layers": sorted(list(self.layers)),
            "components": [c.to_dict() for c in self.components],
            "nets": {name: net.to_dict() for name, net in self.nets.items()},
            "traces": [t.to_dict() for t in self.traces],
            "vias": [v.to_dict() for v in self.vias],
            "zones": [z.to_dict() for z in self.zones],
        }