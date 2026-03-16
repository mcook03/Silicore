from engine.risk import make_risk


def run_rule(pcb):
    risks = []

    required_power_nets = {"VOUT", "GND"}
    existing_nets = set(pcb.nets.keys())

    for net in required_power_nets:
        if net not in existing_nets:
            risks.append(
                make_risk(
                    rule_id="power_rail",
                    severity="critical",
                    message=f"Missing required power rail {net}",
                    nets=[net],
                )
            )

    if "VOUT" in pcb.nets:
        vout_refs = {ref for ref, _ in pcb.nets["VOUT"].connections}
        mcus = [c for c in pcb.components if c.type.strip().upper() == "MCU"]

        for mcu in mcus:
            if mcu.ref not in vout_refs:
                risks.append(
                    make_risk(
                        rule_id="power_rail",
                        severity="high",
                        message=f"{mcu.ref} is not connected to the VOUT power rail",
                        components=[mcu.ref],
                        nets=["VOUT"],
                    )
                )

    if "GND" in pcb.nets:
        gnd_refs = {ref for ref, _ in pcb.nets["GND"].connections}
        for comp in pcb.components:
            if comp.ref not in gnd_refs and comp.type.strip().upper() in {"MCU", "REGULATOR", "MOSFET"}:
                risks.append(
                    make_risk(
                        rule_id="power_rail",
                        severity="high",
                        message=f"{comp.ref} may be missing a ground connection on GND rail",
                        components=[comp.ref],
                        nets=["GND"],
                    )
                )

    return risks