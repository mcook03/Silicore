from engine.risk import make_risk


def _normalize(value):
    return str(value).strip().upper()


def _collect_component_nets(component):
    nets = set()

    connected_nets = getattr(component, "connected_nets", None)
    if connected_nets:
        for net in connected_nets:
            if net:
                nets.add(net)

    if hasattr(component, "get_nets"):
        try:
            getter_nets = component.get_nets() or []
            for net in getter_nets:
                if net:
                    nets.add(net)
        except Exception:
            pass

    net_names = getattr(component, "net_names", None)
    if net_names:
        for net in net_names:
            if net:
                nets.add(net)

    single_net = getattr(component, "net", None)
    if single_net:
        nets.add(single_net)

    net_name = getattr(component, "net_name", None)
    if net_name:
        nets.add(net_name)

    pads = getattr(component, "pads", []) or []
    for pad in pads:
        pad_net_name = getattr(pad, "net_name", None)
        if pad_net_name:
            nets.add(pad_net_name)

    return [_normalize(net) for net in nets if str(net).strip()]


def _matches_any_keyword(net_name, keywords):
    net_name = _normalize(net_name)
    for keyword in keywords:
        keyword = _normalize(keyword)
        if keyword and keyword in net_name:
            return True
    return False


def run_rule(pcb, config):
    risks = []

    power_config = config.get("power", {})
    rules_config = config.get("rules", {})
    power_connectivity_config = rules_config.get("power_connectivity", {})

    required_power_nets = [
        _normalize(net)
        for net in power_connectivity_config.get(
            "required_power_nets",
            power_config.get("required_power_nets", ["VCC", "VIN", "VBAT", "5V", "3V3", "VDD"]),
        )
        if str(net).strip()
    ]

    required_ground_nets = [
        _normalize(net)
        for net in power_connectivity_config.get(
            "required_ground_nets",
            power_config.get("required_ground_nets", ["GND", "GROUND"]),
        )
        if str(net).strip()
    ]

    for component in getattr(pcb, "components", []):
        component_type = _normalize(getattr(component, "type", ""))

        if component_type in ["MOUNT", "MECH", "HOLE"]:
            continue

        nets = _collect_component_nets(component)
        if not nets:
            continue

        has_power = any(_matches_any_keyword(net, required_power_nets) for net in nets)
        has_ground = any(_matches_any_keyword(net, required_ground_nets) for net in nets)

        # Good connectivity: component touches both a power net and a ground net.
        if has_power and has_ground:
            continue

        if has_ground and not has_power:
            severity = "medium"
            message = f"{component.ref} has ground but no visible power rail"
            recommendation = "Verify that the component is connected to the intended supply net as well as ground."
        else:
            severity = "high"
            message = f"{component.ref} is not connected to a valid power rail"
            recommendation = "Connect the component to the intended power net and confirm that its pad-to-net assignments are present in the board data."

        risks.append(
            make_risk(
                rule_id="power_connectivity",
                category="power_integrity",
                severity=severity,
                message=message,
                recommendation=recommendation,
                components=[component.ref],
                nets=nets,
                metrics={
                    "required_power_nets": required_power_nets,
                    "required_ground_nets": required_ground_nets,
                    "observed_component_nets": nets,
                    "has_power": has_power,
                    "has_ground": has_ground,
                },
                confidence=0.8 if severity == "high" else 0.7,
                short_title="Missing power rail" if severity == "high" else "Ground without power",
                fix_priority="high" if severity == "high" else "medium",
                estimated_impact="high" if severity == "high" else "moderate",
                design_domain="power",
            )
        )

    return risks