from collections import defaultdict


def _lower(value):
    return str(value or "").strip().lower()


SUBSYSTEM_KEYWORDS = {
    "power": ["vin", "vcc", "vdd", "vbat", "buck", "boost", "ldo", "pmic", "reg", "phase", "sw", "supply"],
    "clocking": ["clk", "clock", "xtal", "osc", "pll", "refclk", "crystal"],
    "analog": ["adc", "dac", "vref", "opamp", "afe", "sensor", "sense", "analog", "shunt", "ref"],
    "digital_control": ["mcu", "cpu", "soc", "fpga", "dsp", "logic", "controller", "stm", "esp", "pic", "avr"],
    "connectivity": ["usb", "eth", "can", "spi", "i2c", "uart", "pcie", "mipi", "rf", "ble", "wifi", "connector"],
    "debug_test": ["jtag", "swd", "test", "debug", "prog", "boot", "header"],
}


def _match_subsystem(text):
    lowered = _lower(text)
    for subsystem, keywords in SUBSYSTEM_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return subsystem
    return "general"


def classify_pcb_subsystems(pcb):
    components = getattr(pcb, "components", []) or []
    nets = getattr(pcb, "nets", {}) or {}

    subsystem_components = defaultdict(list)
    subsystem_nets = defaultdict(list)
    subsystem_weight = defaultdict(float)

    for component in components:
        text = " ".join(
            [
                getattr(component, "ref", ""),
                getattr(component, "value", ""),
                getattr(component, "type", ""),
                getattr(component, "footprint", ""),
            ]
        )
        subsystem = _match_subsystem(text)
        subsystem_components[subsystem].append(getattr(component, "ref", "UNKNOWN"))
        subsystem_weight[subsystem] += 2.5

    for net_name, connections in (nets or {}).items():
        subsystem = _match_subsystem(net_name)
        subsystem_nets[subsystem].append(net_name)
        connection_count = len(getattr(connections, "connections", []) or []) if hasattr(connections, "connections") else len(connections or [])
        subsystem_weight[subsystem] += 1.0 + (0.15 * connection_count)

    summaries = []
    all_subsystems = set(subsystem_components.keys()) | set(subsystem_nets.keys())
    for subsystem in all_subsystems:
        component_refs = subsystem_components.get(subsystem, [])
        net_names = subsystem_nets.get(subsystem, [])
        summaries.append(
            {
                "name": subsystem,
                "label": subsystem.replace("_", " ").title(),
                "component_count": len(component_refs),
                "net_count": len(net_names),
                "components": component_refs[:12],
                "nets": net_names[:12],
                "weight": round(subsystem_weight.get(subsystem, 0.0), 1),
            }
        )

    summaries.sort(key=lambda item: (-item["weight"], -item["component_count"], -item["net_count"], item["label"].lower()))
    dominant = summaries[0]["label"] if summaries else "General"

    interaction_risks = []
    names = {item["name"] for item in summaries}
    if "power" in names and "analog" in names:
        interaction_risks.append(
            {
                "rule_id": "subsystem_power_analog_interaction",
                "category": "system_interaction",
                "severity": "medium",
                "message": "Power and analog subsystems coexist and may need tighter isolation review.",
                "recommendation": "Inspect regulator, switching, and analog-reference placement to verify noise containment.",
                "design_domain": "power_integrity",
                "confidence": 0.74,
                "fix_priority": "high",
                "short_title": "Power and analog interaction pressure",
                "why_it_matters": "Supply noise or poor partitioning can corrupt sensitive analog behavior.",
            }
        )
    if "clocking" in names and "connectivity" in names:
        interaction_risks.append(
            {
                "rule_id": "subsystem_clock_io_interaction",
                "category": "system_interaction",
                "severity": "medium",
                "message": "Clocking and fast connectivity subsystems share board context and need timing-containment review.",
                "recommendation": "Check clock-source placement, reference continuity, and keepout from high-speed connectors.",
                "design_domain": "signal_integrity",
                "confidence": 0.72,
                "fix_priority": "medium",
                "short_title": "Clock and connectivity interaction pressure",
                "why_it_matters": "Weak clock containment can amplify timing sensitivity and EMI risk.",
            }
        )
    if "debug_test" not in names and "digital_control" in names:
        interaction_risks.append(
            {
                "rule_id": "subsystem_debug_access_gap",
                "category": "system_interaction",
                "severity": "low",
                "message": "Digital control logic is present without a clearly classified debug or test subsystem.",
                "recommendation": "Confirm bring-up access through debug headers, test pads, or programming entry points.",
                "design_domain": "testability",
                "confidence": 0.66,
                "fix_priority": "medium",
                "short_title": "Debug access classification gap",
                "why_it_matters": "Boards are harder to validate when debug access is weak or missing.",
            }
        )

    return {
        "subsystems": summaries,
        "dominant_subsystem": dominant,
        "interaction_risks": interaction_risks,
        "summary": (
            f"Dominant subsystem pressure is {dominant}."
            if summaries else "Subsystem classification is not available for this board."
        ),
    }
