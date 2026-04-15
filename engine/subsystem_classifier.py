from collections import defaultdict


def _lower(value):
    return str(value or "").strip().lower()


SUBSYSTEM_KEYWORDS = {
    "power": ["vin", "vcc", "vdd", "vbat", "buck", "boost", "ldo", "pmic", "reg", "phase", "sw"],
    "clocking": ["clk", "clock", "xtal", "osc", "pll", "refclk"],
    "analog": ["adc", "dac", "vref", "opamp", "afe", "sensor", "sense", "analog", "shunt"],
    "digital_control": ["mcu", "cpu", "soc", "fpga", "dsp", "logic", "controller", "stm", "esp", "pic", "avr"],
    "connectivity": ["usb", "eth", "can", "spi", "i2c", "uart", "pcie", "mipi", "rf", "ble", "wifi", "connector"],
    "debug_test": ["jtag", "swd", "test", "debug", "prog", "boot"],
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

    for net_name in nets.keys():
        subsystem = _match_subsystem(net_name)
        subsystem_nets[subsystem].append(net_name)

    summaries = []
    for subsystem in sorted(set(list(subsystem_components.keys()) + list(subsystem_nets.keys()))):
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
            }
        )

    return {
        "subsystems": summaries,
        "dominant_subsystem": summaries[0]["label"] if summaries else "General",
    }
