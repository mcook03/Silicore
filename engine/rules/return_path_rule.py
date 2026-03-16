def check_return_paths(pcb):
    risks = []

    if "GND" not in pcb.nets:
        risks.append("Risk: No GND net found, return paths cannot be verified")
        return risks

    gnd_refs = {ref for ref, _ in pcb.nets["GND"].connections}

    for net_name, net in pcb.nets.items():
        if net_name in {"GND", "VIN", "VOUT"}:
            continue

        for ref, _ in net.connections:
            component = pcb.get_component(ref)
            if component and component.type.upper() in {"MCU", "MOSFET", "DRIVER"}:
                if ref not in gnd_refs:
                    risks.append(
                        f"Risk: {ref} on signal net {net_name} may not have a proper return path to GND"
                    )

    return risks