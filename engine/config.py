DEFAULT_CONFIG = {
    "rules": {
        "spacing": {
            "enabled": True,
            "threshold": 5.0,
        },
        "decoupling": {
            "enabled": True,
            "threshold": 6.0,
        },
        "thermal": {
            "enabled": True,
            "threshold": 8.0,
        },
        "density": {
            "enabled": True,
            "region_size": 10.0,
            "component_threshold": 4,
        },
        "power_distribution": {
            "enabled": True,
            "threshold": 15.0,
        },
        "power_rail": {
            "enabled": True,
            "min_connections": 2,
            "max_trace_length": 80.0,
            "min_trace_width": 0.25,
            "max_via_count": 6,
        },
        "signal_path": {
            "enabled": True,
            "threshold": 40.0,
        },
        "return_path": {
            "enabled": True,
            "min_ground_zones": 1,
            "require_ground_net": True,
        },
    },
    "scoring": {
        "severity_weights": {
            "low": 0.5,
            "medium": 1.0,
            "high": 1.5,
            "critical": 2.0,
        },
        "category_weights": {
            "layout": 1.0,
            "power_integrity": 1.4,
            "signal_integrity": 1.3,
            "thermal": 1.2,
            "manufacturing": 1.1,
            "reliability": 1.2,
            "other": 1.0,
        },
        "persistent_risk_multiplier": 1.15,
        "floor": 0.0,
        "ceiling": 10.0,
        "start_score": 10.0,
    },
}