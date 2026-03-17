def normalize_pcb(pcb):
    for c in pcb.components:
        if c.type:
            c.type = c.type.lower().strip()
        if c.value:
            c.value = c.value.strip()
        if c.layer:
            c.layer = c.layer.strip()

    normalized_nets = {}
    for name, net in pcb.nets.items():
        clean_name = name.strip().upper()
        net.name = clean_name
        normalized_nets[clean_name] = net

    pcb.nets = normalized_nets

    cleaned_layers = set()
    for layer in pcb.layers:
        cleaned_layers.add(layer.strip())
    pcb.layers = cleaned_layers

    pcb.estimate_board_bounds()
    return pcb