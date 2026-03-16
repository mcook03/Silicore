class Component:
    def __init__(self, ref, value, x, y, layer, comp_type):
        self.ref = ref
        self.value = value
        self.x = float(x)
        self.y = float(y)
        self.layer = layer
        self.type = comp_type
        self.pins = {}

    def add_pin(self, pin_name, net_name):
        self.pins[pin_name] = net_name

    def __repr__(self):
        return (
            f"Component({self.ref}, {self.value}, {self.x}, "
            f"{self.y}, {self.layer}, {self.type})"
        )


class Net:
    def __init__(self, name):
        self.name = name
        self.connections = []

    def add_connection(self, ref, pin):
        self.connections.append((ref, pin))

    def __repr__(self):
        return f"Net({self.name}, connections={self.connections})"


class PCB:
    def __init__(self):
        self.components = []
        self.nets = {}

    def add_component(self, component):
        self.components.append(component)

    def add_net_connection(self, net_name, ref, pin):
        if net_name not in self.nets:
            self.nets[net_name] = Net(net_name)
        self.nets[net_name].add_connection(ref, pin)

        component = self.get_component(ref)
        if component:
            component.add_pin(pin, net_name)

    def get_component(self, ref):
        for component in self.components:
            if component.ref == ref:
                return component
        return None