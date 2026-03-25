DEFAULT_CONFIG = {
    # =========================
    # SCORING (DO NOT CHANGE YET)
    # =========================
    "score": {
        "start_score": 10.0,
        "penalties": {
            "low": 0.5,
            "medium": 1.0,
            "high": 1.5,
            "critical": 2.0,
        }
    },

    # =========================
    # LAYOUT RULES
    # =========================
    "layout": {
        "min_component_spacing": 5.0,
        "max_density_threshold": 5,  # components per region
    },

    # =========================
    # POWER RULES
    # =========================
    "power": {
        "required_power_nets": ["VCC", "3V3", "5V", "VIN"],
        "required_ground_nets": ["GND", "GROUND"],
        "max_power_distance": 50.0,
    },

    # =========================
    # SIGNAL / TRACE RULES
    # =========================
    "signal": {
        "max_trace_length": 50,
        "critical_nets": ["CLK", "DATA", "CTRL"],
    },

    # =========================
    # THERMAL RULES
    # =========================
    "thermal": {
        "max_hotspot_distance": 5.0,
    },

    # =========================
    # EMI / RETURN PATH
    # =========================
    "emi": {
        "require_ground_reference": True,
    }
}