from engine.risk import make_risk


def _component_nets(component):
    nets = set()
    for pad in getattr(component, "pads", []):
        if getattr(pad, "net_name", None):
            nets.add(str(pad.net_name).strip().upper())
    return nets


def _is_resistor(component):
    ref = str(getattr(component, "ref", "")).upper()
    component_type = str(getattr(component, "type", "")).lower()
    return ref.startswith("R") or "resistor" in component_type


def run_rule(pcb, config):
    risks = []
    rule_config = config.get("rules", {}).get("component_analysis", {})

    pull_keywords = [
        str(item).strip().upper()
        for item in rule_config.get(
            "pull_sensitive_net_keywords",
            ["RESET", "RST", "EN", "BOOT", "CS", "INT", "IRQ"],
        )
        if str(item).strip()
    ]
    termination_keywords = [
        str(item).strip().upper()
        for item in rule_config.get(
            "termination_net_keywords",
            ["CLK", "USB", "DDR", "PCIE", "ETH"],
        )
        if str(item).strip()
    ]
    termination_length_threshold = float(rule_config.get("termination_length_threshold", 18.0))

    net_to_components = {}
    for component in getattr(pcb, "components", []):
        for net_name in _component_nets(component):
            net_to_components.setdefault(net_name, []).append(component)

    for net_name, components in net_to_components.items():
        upper_net = str(net_name).strip().upper()
        has_resistor = any(_is_resistor(component) for component in components)

        if any(keyword in upper_net for keyword in pull_keywords) and not has_resistor:
            risks.append(
                make_risk(
                    rule_id="component_analysis",
                    category="component_design",
                    severity="medium",
                    message=f"Control net {upper_net} has no visible pull resistor component",
                    recommendation="Review whether this control or boot-related net should include an explicit pull-up or pull-down resistor.",
                    components=[component.ref for component in components[:4]],
                    nets=[upper_net],
                    metrics={
                        "component_count": len(components),
                        "has_resistor": has_resistor,
                    },
                    confidence=0.72,
                    short_title="Possible missing pull resistor",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="component",
                    why_it_matters="Boot, reset, chip-select, and interrupt nets often need a defined default state to behave reliably.",
                    trigger_condition="A control-sensitive net was identified without a visible pull resistor on the connected component set.",
                    threshold_label="Expected pull resistor presence on control-sensitive nets",
                    observed_label="Observed pull resistor presence: none",
                )
            )

        total_length = pcb.total_trace_length_for_net(upper_net)
        if any(keyword in upper_net for keyword in termination_keywords) and total_length >= termination_length_threshold and not has_resistor:
            risks.append(
                make_risk(
                    rule_id="component_analysis",
                    category="component_design",
                    severity="medium",
                    message=f"High-speed net {upper_net} has a long route with no visible series or termination resistor",
                    recommendation="Review whether this interface requires termination or series damping based on edge rate and topology.",
                    components=[component.ref for component in components[:4]],
                    nets=[upper_net],
                    metrics={
                        "trace_length": round(total_length, 2),
                        "threshold": termination_length_threshold,
                        "has_resistor": has_resistor,
                    },
                    confidence=0.7,
                    short_title="Possible missing signal termination",
                    fix_priority="medium",
                    estimated_impact="moderate",
                    design_domain="component",
                    why_it_matters="Longer high-speed routes can require series damping or termination to control ringing and reflections.",
                    trigger_condition="A high-speed net exceeded the termination review length threshold without a visible resistor component.",
                    threshold_label=f"Termination review length {termination_length_threshold:.2f} units",
                    observed_label=f"Observed route length {total_length:.2f} units",
                )
            )

    return risks
