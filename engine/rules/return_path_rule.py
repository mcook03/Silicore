from engine.risk import make_risk


def run_rule(pcb):
    risks = []

    if "GND" not in pcb.nets:
        risks.append(
            make_risk(
                rule_id="return_path",
                category="emi_return_path",
                severity="critical",
                message="No GND net found, return paths cannot be verified",
                recommendation="Add a valid ground net so return current paths can be analyzed.",
                nets=["GND"],
            )
        )
        return risks

    gnd_refs = {ref for ref, _ in pcb.nets["GND"].connections}

    for net_name, net in pcb.nets.items():
        if net_name in {"GND", "VIN", "VOUT"}:
            continue

        for ref, _ in net.connections:
            component = pcb.get_component(ref)
            if component and component.type.strip().upper() in {"MCU", "MOSFET", "DRIVER"}:
                if ref not in gnd_refs:
                    risks.append(
                        make_risk(
                            rule_id="return_path",
                            category="emi_return_path",
                            severity="high",
                            message=f"{ref} on signal net {net_name} may not have a proper return path to GND",
                            recommendation="Ensure the signal has a nearby ground return path to reduce EMI and instability.",
                            components=[ref],
                            nets=[net_name, "GND"],
                        )
                    )

    return risks