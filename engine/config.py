import copy
import json
import os

CONFIG_FILE = "silicore_config.json"


DEFAULT_CONFIG = {
    "analysis": {
        "profile": "balanced",
        "board_type": "general",
        "category_toggles": {
            "layout_manufacturing": True,
            "power": True,
            "signal": True,
            "thermal": True,
            "emi_reliability": True,
            "safety": True,
        },
        "rule_toggles": {},
    },
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
        "density_threshold": 6,
        "density_region_size": 25.0
    },
    "power": {
        "required_power_nets": ["VCC", "VIN"],
        "required_ground_nets": ["GND"],
        "distribution_distance_threshold": 20.0,
        "decoupling_distance_threshold": 4.0,
        "max_trace_length": 50.0,
        "min_trace_width": 0.5,
        "max_via_count": 5,
        "min_connections": 2
    },
    "signal": {
        "max_trace_length": 25.0,
        "critical_nets": ["CLK", "SCL", "SDA", "MOSI", "MISO", "CS"],
        "min_general_trace_width": 0.15,
        "excluded_net_keywords": ["GND", "GROUND", "VCC", "VIN", "VBAT", "3V3", "5V", "12V", "VDD"]
    },
    "thermal": {
        "hotspot_distance_threshold": 4.0
    },
    "emi": {
        "require_ground_reference": True
    },
    "rules": {
        "spacing": {},
        "density": {},
        "thermal": {},
        "decoupling": {},
        "power_distribution": {},
        "return_path": {},
        "signal_path": {},
        "power_rail": {},
        "trace_quality": {},
        "signal_integrity_advanced": {
            "max_signal_vias": 2,
            "width_ratio_threshold": 2.2,
            "detour_ratio_threshold": 1.8,
            "stub_length_threshold": 12.0,
            "crosstalk_spacing_threshold": 2.5,
        },
        "differential_pair": {
            "length_mismatch_threshold": 5.0,
            "via_mismatch_threshold": 1,
        },
        "manufacturability": {
            "min_trace_width": 0.15,
            "min_drill": 0.2,
            "min_annular_ring": 0.1,
            "via_in_pad_distance": 0.35,
        },
        "thermal_management": {
            "thermal_via_radius": 4.0,
            "min_thermal_vias": 1,
            "min_heat_spread_width": 0.5,
        },
        "reliability": {
            "min_ground_vias": 2,
            "min_ground_connections": 4,
        },
        "component_analysis": {
            "termination_length_threshold": 18.0,
        },
        "emi_emc": {
            "max_switch_trace_length": 18.0,
            "sensitive_keepout": 6.0,
            "return_via_radius": 3.0,
            "max_loop_length": 45.0,
        },
        "stackup_return_path": {
            "max_signal_layers": 2,
            "signal_via_ground_radius": 3.5,
            "max_two_layer_critical_length": 28.0,
        },
        "assembly_testability": {
            "min_fiducials": 2,
            "probe_access_radius": 6.0,
            "min_ground_test_points": 1,
        },
        "safety_high_voltage": {
            "min_clearance": 2.5,
            "min_creepage": 5.0,
            "high_voltage_net_keywords": ["HV", "VAC", "VDC", "VBUS", "48V", "24V", "PACK", "BATT"],
        },
        "power_path_realism": {
            "neckdown_ratio_threshold": 2.5,
            "max_high_current_length": 40.0,
            "converter_cap_radius": 7.0,
            "max_high_current_vias": 4,
        },
    }
}


def deep_merge(default, custom):
    result = copy.deepcopy(default)

    for key, value in custom.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                return deep_merge(DEFAULT_CONFIG, data)
        except Exception:
            return copy.deepcopy(DEFAULT_CONFIG)
    return copy.deepcopy(DEFAULT_CONFIG)


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


ACTIVE_CONFIG = load_config()


def get_config():
    return ACTIVE_CONFIG


def update_config_from_form(form):
    try:
        # Layout
        ACTIVE_CONFIG["layout"]["min_component_spacing"] = float(
            form.get("layout_min_component_spacing", 3.0)
        )
        ACTIVE_CONFIG["layout"]["density_threshold"] = int(
            float(form.get("layout_density_threshold", 6))
        )
        ACTIVE_CONFIG["layout"]["density_region_size"] = float(
            form.get("layout_density_region_size", 25.0)
        )

        # Power nets
        power_nets = form.get("power_required_power_nets", "")
        ground_nets = form.get("power_required_ground_nets", "")

        ACTIVE_CONFIG["power"]["required_power_nets"] = [
            x.strip() for x in power_nets.split(",") if x.strip()
        ]
        ACTIVE_CONFIG["power"]["required_ground_nets"] = [
            x.strip() for x in ground_nets.split(",") if x.strip()
        ]

        # Power thresholds
        ACTIVE_CONFIG["power"]["distribution_distance_threshold"] = float(
            form.get("power_distribution_distance_threshold", 20.0)
        )
        ACTIVE_CONFIG["power"]["decoupling_distance_threshold"] = float(
            form.get("power_decoupling_distance_threshold", 4.0)
        )
        ACTIVE_CONFIG["power"]["max_trace_length"] = float(
            form.get("power_max_trace_length", 50.0)
        )
        ACTIVE_CONFIG["power"]["min_trace_width"] = float(
            form.get("power_min_trace_width", 0.5)
        )
        ACTIVE_CONFIG["power"]["max_via_count"] = int(
            float(form.get("power_max_via_count", 5))
        )

        # Signal
        ACTIVE_CONFIG["signal"]["max_trace_length"] = float(
            form.get("signal_max_trace_length", 25.0)
        )

        critical_nets = form.get("signal_critical_nets", "")
        ACTIVE_CONFIG["signal"]["critical_nets"] = [
            x.strip() for x in critical_nets.split(",") if x.strip()
        ]

        # Thermal
        ACTIVE_CONFIG["thermal"]["hotspot_distance_threshold"] = float(
            form.get("thermal_hotspot_distance_threshold", 4.0)
        )

        # EMI
        emi_value = str(form.get("emi_require_ground_reference", "true")).lower()
        ACTIVE_CONFIG["emi"]["require_ground_reference"] = emi_value in [
            "true", "1", "yes", "on"
        ]

        save_config(ACTIVE_CONFIG)

    except Exception as e:
        print("Config update error:", e)

    return ACTIVE_CONFIG
