class Component:
    def __init__(self, ref, value, x, y, layer, comp_type):
        self.ref = ref
        self.value = value
        self.x = float(x)
        self.y = float(y)
        self.layer = layer
        self.type = comp_type

    def __repr__(self):
        return f"Component({self.ref}, {self.value}, {self.x}, {self.y}, {self.layer}, {self.type})"


class PCB:
    def __init__(self):
        self.components = []

    def add_component(self, component):
        self.components.append(component)