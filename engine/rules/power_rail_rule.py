def check_power_rails(pcb):
    risks = []

    required_power_nets = {"VOUT", "GND"}
    existing_nets = set(pcb.nets.keys())

    for net in required_power_nets:
        if net not in existing_nets:
            risks.append(f"Risk: Missing required power rail {net}")

    if "VOUT" in pcb.nets:
        vout_refs = {ref for ref, _ in pcb.nets["VOUT"].connections}
        mcus = [c for c in pcb.components if c.type.strip().upper() == "MCU"]

        for mcu in mcus:
            if mcu.ref not in vout_refs:
                risks.append(
                    f"Risk: {mcu.ref} is not connected to the VOUT power rail"
                )

    if "GND" in pcb.nets:
        gnd_refs = {ref for ref, _ in pcb.nets["GND"].connections}
        for comp in pcb.components:
            if comp.ref not in gnd_refs and comp.type.upper() in {"MCU", "REGULATOR", "MOSFET"}:
                risks.append(
                    f"Risk: {comp.ref} may be missing a ground connection on GND rail"
                )

    return risks