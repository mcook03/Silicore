class Component:

    def __init__(self, ref, value, x, y, layer, comp_type="generic"):
        self.ref = ref
        self.value = value
        self.x = x
        self.y = y
        self.layer = layer
        self.type = comp_type

    def position(self):
        return (self.x, self.y)


class PCB:

    def __init__(self):
        self.components = []

    def add_component(self, component):
        self.components.append(component)

    def get_components(self):
        return self.components