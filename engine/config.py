DEFAULT_CONFIG = {
    "score": {
        "start_score": 10.0,
        "min_score": 0.0,
        "max_score": 10.0,
        "severity_penalties": {
            "low": 0.5,
            "medium": 1.0,
            "high": 1.5,
            "critical": 2.0
        }
    },
    "layout": {
        "min_component_spacing": 3.0,
        "density_threshold": 6
    },
    "power": {
        "required_power_nets": ["VCC", "VIN"],
        "required_ground_nets": ["GND"]
    },
    "signal": {
        "max_trace_length": 25.0,
        "critical_nets": ["CLK", "SCL", "SDA", "MOSI", "MISO", "CS"]
    },
    "thermal": {
        "hotspot_distance_threshold": 4.0
    },
    "emi": {
        "require_ground_reference": True
    }
}