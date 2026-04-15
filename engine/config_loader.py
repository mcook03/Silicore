import json
import os
from copy import deepcopy

from engine.config import DEFAULT_CONFIG

ANALYSIS_PROFILE_PRESETS = {
    "balanced": {},
    "high_speed": {
        "signal": {
            "critical_nets": ["CLK", "USB", "DDR", "PCIE", "ETH", "MIPI", "CAN", "REFCLK"],
            "max_trace_length": 22.0,
        },
        "rules": {
            "signal_integrity_advanced": {
                "max_signal_vias": 1,
                "width_ratio_threshold": 1.8,
                "detour_ratio_threshold": 1.45,
                "stub_length_threshold": 8.0,
                "crosstalk_spacing_threshold": 4.0,
            },
            "differential_pair": {
                "length_mismatch_threshold": 3.0,
                "via_mismatch_threshold": 0,
            },
            "stackup_return_path": {
                "max_signal_layers": 2,
                "signal_via_ground_radius": 2.5,
                "max_two_layer_critical_length": 20.0,
            },
            "clock_sensitive_placement": {
                "max_clock_source_distance": 8.0,
                "sensitive_aggressor_keepout": 10.0,
            },
        },
    },
    "power_delivery": {
        "power": {
            "distribution_distance_threshold": 16.0,
            "decoupling_distance_threshold": 3.0,
            "min_trace_width": 0.8,
            "max_via_count": 4,
        },
        "rules": {
            "power_path_realism": {
                "neckdown_ratio_threshold": 1.9,
                "max_high_current_length": 28.0,
                "converter_cap_radius": 5.5,
                "max_high_current_vias": 2,
            },
            "thermal_management": {
                "min_thermal_vias": 2,
                "min_heat_spread_width": 0.8,
            },
            "emi_emc": {
                "max_loop_length": 28.0,
                "max_switch_trace_length": 12.0,
            },
        },
    },
    "mixed_signal": {
        "power": {
            "required_ground_nets": ["GND", "AGND", "DGND"],
        },
        "rules": {
            "emi_emc": {
                "sensitive_keepout": 8.0,
            },
            "stackup_return_path": {
                "signal_via_ground_radius": 3.0,
            },
            "component_analysis": {
                "termination_length_threshold": 16.0,
            },
            "clock_sensitive_placement": {
                "max_clock_source_distance": 10.0,
                "sensitive_aggressor_keepout": 12.0,
            },
        },
    },
    "production_readiness": {
        "layout": {
            "min_component_spacing": 4.0,
        },
        "rules": {
            "manufacturability": {
                "min_drill": 0.25,
                "min_annular_ring": 0.12,
                "via_in_pad_distance": 0.45,
            },
            "assembly_testability": {
                "min_fiducials": 2,
                "probe_access_radius": 7.0,
                "min_ground_test_points": 1,
            },
        },
    },
    "high_voltage": {
        "rules": {
            "safety_high_voltage": {
                "min_clearance": 4.0,
                "min_creepage": 8.0,
                "high_voltage_net_keywords": ["HV", "VAC", "VDC", "VBUS", "48V", "24V", "PACK", "BATT", "MAINS"],
            },
            "manufacturability": {
                "via_in_pad_distance": 0.5,
            },
        },
    },
}

SUPPORTED_ANALYSIS_PROFILES = tuple(sorted(list(ANALYSIS_PROFILE_PRESETS.keys()) + ["custom"]))


EDITABLE_FIELD_MAP = {
    "analysis": {
        "profile": {
            "type": "str",
            "form_keys": ["analysis_profile", "profile"],
        },
        "board_type": {
            "type": "str",
            "form_keys": ["analysis_board_type", "board_type"],
        },
        "custom_profile_name": {
            "type": "str",
            "form_keys": ["analysis_custom_profile_name", "custom_profile_name"],
        },
        "toggle_layout_manufacturing": {
            "type": "bool",
            "form_keys": ["analysis_toggle_layout_manufacturing"],
            "config_path": ["category_toggles", "layout_manufacturing"],
        },
        "toggle_power": {
            "type": "bool",
            "form_keys": ["analysis_toggle_power"],
            "config_path": ["category_toggles", "power"],
        },
        "toggle_signal": {
            "type": "bool",
            "form_keys": ["analysis_toggle_signal"],
            "config_path": ["category_toggles", "signal"],
        },
        "toggle_thermal": {
            "type": "bool",
            "form_keys": ["analysis_toggle_thermal"],
            "config_path": ["category_toggles", "thermal"],
        },
        "toggle_emi_reliability": {
            "type": "bool",
            "form_keys": ["analysis_toggle_emi_reliability"],
            "config_path": ["category_toggles", "emi_reliability"],
        },
        "toggle_safety": {
            "type": "bool",
            "form_keys": ["analysis_toggle_safety"],
            "config_path": ["category_toggles", "safety"],
        },
    },
    "layout": {
        "min_component_spacing": {
            "type": "float",
            "form_keys": ["layout_min_component_spacing", "min_component_spacing"],
            "rules_targets": [("spacing", "threshold")],
        },
        "density_threshold": {
            "type": "int",
            "form_keys": ["layout_density_threshold", "density_threshold"],
            "rules_targets": [("density", "component_threshold")],
        },
        "density_region_size": {
            "type": "float",
            "form_keys": ["layout_density_region_size", "density_region_size"],
            "rules_targets": [("density", "region_size")],
        },
    },
    "power": {
        "required_power_nets": {
            "type": "list",
            "form_keys": ["power_required_power_nets", "required_power_nets"],
            "rules_targets": [("power_connectivity", "required_power_nets")],
        },
        "required_ground_nets": {
            "type": "list",
            "form_keys": ["power_required_ground_nets", "required_ground_nets"],
            "rules_targets": [
                ("power_connectivity", "required_ground_nets"),
                ("ground_reference", "ground_net_keywords"),
                ("return_path", "ground_net_keywords"),
            ],
        },
        "distribution_distance_threshold": {
            "type": "float",
            "form_keys": ["power_distribution_distance_threshold", "distribution_distance_threshold"],
            "rules_targets": [("power_distribution", "threshold")],
        },
        "decoupling_distance_threshold": {
            "type": "float",
            "form_keys": ["power_decoupling_distance_threshold", "decoupling_distance_threshold"],
            "rules_targets": [("decoupling", "threshold")],
        },
        "max_trace_length": {
            "type": "float",
            "form_keys": ["power_max_trace_length", "max_trace_length"],
            "rules_targets": [("power_rail", "max_trace_length")],
        },
        "min_trace_width": {
            "type": "float",
            "form_keys": ["power_min_trace_width", "min_trace_width"],
            "rules_targets": [("power_rail", "min_trace_width")],
        },
        "max_via_count": {
            "type": "int",
            "form_keys": ["power_max_via_count", "max_via_count"],
            "rules_targets": [("power_rail", "max_via_count")],
        },
        "min_connections": {
            "type": "int",
            "form_keys": ["power_min_connections", "min_connections"],
            "rules_targets": [("power_rail", "min_connections")],
        },
    },
    "signal": {
        "max_trace_length": {
            "type": "float",
            "form_keys": ["signal_max_trace_length", "max_trace_length"],
            "rules_targets": [
                ("signal_path", "threshold"),
                ("net_length", "max_trace_length"),
            ],
        },
        "critical_nets": {
            "type": "list",
            "form_keys": ["signal_critical_nets", "critical_nets"],
            "rules_targets": [
                ("net_length", "critical_nets"),
                ("ground_reference", "critical_net_keywords"),
                ("return_path", "critical_net_keywords"),
            ],
        },
        "min_general_trace_width": {
            "type": "float",
            "form_keys": ["signal_min_general_trace_width", "min_general_trace_width"],
            "rules_targets": [("trace_quality", "min_general_trace_width")],
        },
        "excluded_net_keywords": {
            "type": "list",
            "form_keys": ["signal_excluded_net_keywords", "excluded_net_keywords"],
            "rules_targets": [
                ("trace_quality", "excluded_net_keywords"),
                ("signal_path", "excluded_nets"),
            ],
        },
    },
    "thermal": {
        "hotspot_distance_threshold": {
            "type": "float",
            "form_keys": ["thermal_hotspot_distance_threshold", "hotspot_distance_threshold"],
            "rules_targets": [("thermal", "threshold")],
        },
    },
    "emi": {
        "require_ground_reference": {
            "type": "bool",
            "form_keys": ["emi_require_ground_reference", "require_ground_reference"],
            "rules_targets": [("return_path", "require_ground_reference")],
        },
    },
    "score": {
        "penalty_low": {
            "type": "float",
            "form_keys": ["score_penalty_low"],
            "config_path": ["severity_penalties", "low"],
        },
        "penalty_medium": {
            "type": "float",
            "form_keys": ["score_penalty_medium"],
            "config_path": ["severity_penalties", "medium"],
        },
        "penalty_high": {
            "type": "float",
            "form_keys": ["score_penalty_high"],
            "config_path": ["severity_penalties", "high"],
        },
        "penalty_critical": {
            "type": "float",
            "form_keys": ["score_penalty_critical"],
            "config_path": ["severity_penalties", "critical"],
        },
    },
    "rules": {
        "signal_integrity_max_signal_vias": {
            "type": "int",
            "form_keys": ["signal_integrity_max_signal_vias"],
            "config_path": ["signal_integrity_advanced", "max_signal_vias"],
        },
        "signal_integrity_width_ratio_threshold": {
            "type": "float",
            "form_keys": ["signal_integrity_width_ratio_threshold"],
            "config_path": ["signal_integrity_advanced", "width_ratio_threshold"],
        },
        "signal_integrity_detour_ratio_threshold": {
            "type": "float",
            "form_keys": ["signal_integrity_detour_ratio_threshold"],
            "config_path": ["signal_integrity_advanced", "detour_ratio_threshold"],
        },
        "signal_integrity_stub_length_threshold": {
            "type": "float",
            "form_keys": ["signal_integrity_stub_length_threshold"],
            "config_path": ["signal_integrity_advanced", "stub_length_threshold"],
        },
        "signal_integrity_crosstalk_spacing_threshold": {
            "type": "float",
            "form_keys": ["signal_integrity_crosstalk_spacing_threshold"],
            "config_path": ["signal_integrity_advanced", "crosstalk_spacing_threshold"],
        },
        "differential_pair_length_mismatch_threshold": {
            "type": "float",
            "form_keys": ["differential_pair_length_mismatch_threshold"],
            "config_path": ["differential_pair", "length_mismatch_threshold"],
        },
        "differential_pair_via_mismatch_threshold": {
            "type": "int",
            "form_keys": ["differential_pair_via_mismatch_threshold"],
            "config_path": ["differential_pair", "via_mismatch_threshold"],
        },
        "manufacturing_min_drill": {
            "type": "float",
            "form_keys": ["manufacturing_min_drill"],
            "config_path": ["manufacturability", "min_drill"],
        },
        "manufacturing_min_annular_ring": {
            "type": "float",
            "form_keys": ["manufacturing_min_annular_ring"],
            "config_path": ["manufacturability", "min_annular_ring"],
        },
        "manufacturing_via_in_pad_distance": {
            "type": "float",
            "form_keys": ["manufacturing_via_in_pad_distance"],
            "config_path": ["manufacturability", "via_in_pad_distance"],
        },
        "thermal_management_min_thermal_vias": {
            "type": "int",
            "form_keys": ["thermal_management_min_thermal_vias"],
            "config_path": ["thermal_management", "min_thermal_vias"],
        },
        "thermal_management_via_radius": {
            "type": "float",
            "form_keys": ["thermal_management_via_radius"],
            "config_path": ["thermal_management", "thermal_via_radius"],
        },
        "thermal_management_min_heat_spread_width": {
            "type": "float",
            "form_keys": ["thermal_management_min_heat_spread_width"],
            "config_path": ["thermal_management", "min_heat_spread_width"],
        },
        "reliability_min_ground_vias": {
            "type": "int",
            "form_keys": ["reliability_min_ground_vias"],
            "config_path": ["reliability", "min_ground_vias"],
        },
        "reliability_min_ground_connections": {
            "type": "int",
            "form_keys": ["reliability_min_ground_connections"],
            "config_path": ["reliability", "min_ground_connections"],
        },
        "component_analysis_termination_length_threshold": {
            "type": "float",
            "form_keys": ["component_analysis_termination_length_threshold"],
            "config_path": ["component_analysis", "termination_length_threshold"],
        },
        "clock_sensitive_placement_max_clock_source_distance": {
            "type": "float",
            "form_keys": ["clock_sensitive_placement_max_clock_source_distance"],
            "config_path": ["clock_sensitive_placement", "max_clock_source_distance"],
        },
        "clock_sensitive_placement_sensitive_aggressor_keepout": {
            "type": "float",
            "form_keys": ["clock_sensitive_placement_sensitive_aggressor_keepout"],
            "config_path": ["clock_sensitive_placement", "sensitive_aggressor_keepout"],
        },
        "emi_emc_max_switch_trace_length": {
            "type": "float",
            "form_keys": ["emi_emc_max_switch_trace_length"],
            "config_path": ["emi_emc", "max_switch_trace_length"],
        },
        "emi_emc_sensitive_keepout": {
            "type": "float",
            "form_keys": ["emi_emc_sensitive_keepout"],
            "config_path": ["emi_emc", "sensitive_keepout"],
        },
        "emi_emc_return_via_radius": {
            "type": "float",
            "form_keys": ["emi_emc_return_via_radius"],
            "config_path": ["emi_emc", "return_via_radius"],
        },
        "emi_emc_max_loop_length": {
            "type": "float",
            "form_keys": ["emi_emc_max_loop_length"],
            "config_path": ["emi_emc", "max_loop_length"],
        },
        "stackup_return_path_max_signal_layers": {
            "type": "int",
            "form_keys": ["stackup_return_path_max_signal_layers"],
            "config_path": ["stackup_return_path", "max_signal_layers"],
        },
        "stackup_return_path_signal_via_ground_radius": {
            "type": "float",
            "form_keys": ["stackup_return_path_signal_via_ground_radius"],
            "config_path": ["stackup_return_path", "signal_via_ground_radius"],
        },
        "stackup_return_path_max_two_layer_critical_length": {
            "type": "float",
            "form_keys": ["stackup_return_path_max_two_layer_critical_length"],
            "config_path": ["stackup_return_path", "max_two_layer_critical_length"],
        },
        "assembly_testability_min_fiducials": {
            "type": "int",
            "form_keys": ["assembly_testability_min_fiducials"],
            "config_path": ["assembly_testability", "min_fiducials"],
        },
        "assembly_testability_probe_access_radius": {
            "type": "float",
            "form_keys": ["assembly_testability_probe_access_radius"],
            "config_path": ["assembly_testability", "probe_access_radius"],
        },
        "assembly_testability_min_ground_test_points": {
            "type": "int",
            "form_keys": ["assembly_testability_min_ground_test_points"],
            "config_path": ["assembly_testability", "min_ground_test_points"],
        },
        "safety_high_voltage_min_clearance": {
            "type": "float",
            "form_keys": ["safety_high_voltage_min_clearance"],
            "config_path": ["safety_high_voltage", "min_clearance"],
        },
        "safety_high_voltage_min_creepage": {
            "type": "float",
            "form_keys": ["safety_high_voltage_min_creepage"],
            "config_path": ["safety_high_voltage", "min_creepage"],
        },
        "safety_high_voltage_net_keywords": {
            "type": "list",
            "form_keys": ["safety_high_voltage_net_keywords"],
            "config_path": ["safety_high_voltage", "high_voltage_net_keywords"],
        },
        "power_path_realism_neckdown_ratio_threshold": {
            "type": "float",
            "form_keys": ["power_path_realism_neckdown_ratio_threshold"],
            "config_path": ["power_path_realism", "neckdown_ratio_threshold"],
        },
        "power_path_realism_max_high_current_length": {
            "type": "float",
            "form_keys": ["power_path_realism_max_high_current_length"],
            "config_path": ["power_path_realism", "max_high_current_length"],
        },
        "power_path_realism_converter_cap_radius": {
            "type": "float",
            "form_keys": ["power_path_realism_converter_cap_radius"],
            "config_path": ["power_path_realism", "converter_cap_radius"],
        },
        "power_path_realism_max_high_current_vias": {
            "type": "int",
            "form_keys": ["power_path_realism_max_high_current_vias"],
            "config_path": ["power_path_realism", "max_high_current_vias"],
        },
    },
}


def _deep_merge(base, override):
    result = deepcopy(base)

    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)

    return result


def load_config(config_path="custom_config.json"):
    config = deepcopy(DEFAULT_CONFIG)

    if not os.path.exists(config_path):
        return config

    try:
        with open(config_path, "r", encoding="utf-8") as file:
            custom_config = json.load(file)

        if not isinstance(custom_config, dict):
            return config

        return _deep_merge(config, custom_config)
    except (json.JSONDecodeError, OSError):
        return config


def save_config(config_data, config_path="custom_config.json"):
    with open(config_path, "w", encoding="utf-8") as file:
        json.dump(config_data, file, indent=4)


def get_editable_config_view(config):
    return {
        "analysis": {
            "profile": config.get("analysis", {}).get("profile", "balanced"),
            "board_type": config.get("analysis", {}).get("board_type", "general"),
            "custom_profile_name": config.get("analysis", {}).get("custom_profile_name", DEFAULT_CONFIG["analysis"]["custom_profile_name"]),
            "category_toggles": config.get("analysis", {}).get("category_toggles", {}),
            "available_profiles": list(SUPPORTED_ANALYSIS_PROFILES),
            "available_board_types": ["general", "high_speed", "power", "mixed_signal", "analog", "rf", "industrial"],
        },
        "layout": {
            "min_component_spacing": config.get("layout", {}).get("min_component_spacing"),
            "density_threshold": config.get("layout", {}).get("density_threshold"),
            "density_region_size": config.get("layout", {}).get("density_region_size"),
        },
        "power": {
            "required_power_nets": config.get("power", {}).get("required_power_nets", []),
            "required_ground_nets": config.get("power", {}).get("required_ground_nets", []),
            "distribution_distance_threshold": config.get("power", {}).get("distribution_distance_threshold"),
            "decoupling_distance_threshold": config.get("power", {}).get("decoupling_distance_threshold"),
            "max_trace_length": config.get("power", {}).get("max_trace_length"),
            "min_trace_width": config.get("power", {}).get("min_trace_width"),
            "max_via_count": config.get("power", {}).get("max_via_count"),
            "min_connections": config.get("power", {}).get("min_connections"),
        },
        "signal": {
            "max_trace_length": config.get("signal", {}).get("max_trace_length"),
            "critical_nets": config.get("signal", {}).get("critical_nets", []),
            "min_general_trace_width": config.get("signal", {}).get("min_general_trace_width"),
            "excluded_net_keywords": config.get("signal", {}).get("excluded_net_keywords", []),
        },
        "thermal": {
            "hotspot_distance_threshold": config.get("thermal", {}).get("hotspot_distance_threshold"),
        },
        "emi": {
            "require_ground_reference": config.get("emi", {}).get("require_ground_reference", True),
        },
        "score": {
            "penalty_low": config.get("score", {}).get("severity_penalties", {}).get("low"),
            "penalty_medium": config.get("score", {}).get("severity_penalties", {}).get("medium"),
            "penalty_high": config.get("score", {}).get("severity_penalties", {}).get("high"),
            "penalty_critical": config.get("score", {}).get("severity_penalties", {}).get("critical"),
        },
        "rules": {
            "signal_integrity_max_signal_vias": config.get("rules", {}).get("signal_integrity_advanced", {}).get("max_signal_vias"),
            "signal_integrity_width_ratio_threshold": config.get("rules", {}).get("signal_integrity_advanced", {}).get("width_ratio_threshold"),
            "signal_integrity_detour_ratio_threshold": config.get("rules", {}).get("signal_integrity_advanced", {}).get("detour_ratio_threshold"),
            "signal_integrity_stub_length_threshold": config.get("rules", {}).get("signal_integrity_advanced", {}).get("stub_length_threshold"),
            "signal_integrity_crosstalk_spacing_threshold": config.get("rules", {}).get("signal_integrity_advanced", {}).get("crosstalk_spacing_threshold"),
            "differential_pair_length_mismatch_threshold": config.get("rules", {}).get("differential_pair", {}).get("length_mismatch_threshold"),
            "differential_pair_via_mismatch_threshold": config.get("rules", {}).get("differential_pair", {}).get("via_mismatch_threshold"),
            "manufacturing_min_drill": config.get("rules", {}).get("manufacturability", {}).get("min_drill"),
            "manufacturing_min_annular_ring": config.get("rules", {}).get("manufacturability", {}).get("min_annular_ring"),
            "manufacturing_via_in_pad_distance": config.get("rules", {}).get("manufacturability", {}).get("via_in_pad_distance"),
            "thermal_management_min_thermal_vias": config.get("rules", {}).get("thermal_management", {}).get("min_thermal_vias"),
            "thermal_management_via_radius": config.get("rules", {}).get("thermal_management", {}).get("thermal_via_radius"),
            "thermal_management_min_heat_spread_width": config.get("rules", {}).get("thermal_management", {}).get("min_heat_spread_width"),
            "reliability_min_ground_vias": config.get("rules", {}).get("reliability", {}).get("min_ground_vias"),
            "reliability_min_ground_connections": config.get("rules", {}).get("reliability", {}).get("min_ground_connections"),
            "component_analysis_termination_length_threshold": config.get("rules", {}).get("component_analysis", {}).get("termination_length_threshold"),
            "clock_sensitive_placement_max_clock_source_distance": config.get("rules", {}).get("clock_sensitive_placement", {}).get("max_clock_source_distance"),
            "clock_sensitive_placement_sensitive_aggressor_keepout": config.get("rules", {}).get("clock_sensitive_placement", {}).get("sensitive_aggressor_keepout"),
            "emi_emc_max_switch_trace_length": config.get("rules", {}).get("emi_emc", {}).get("max_switch_trace_length"),
            "emi_emc_sensitive_keepout": config.get("rules", {}).get("emi_emc", {}).get("sensitive_keepout"),
            "emi_emc_return_via_radius": config.get("rules", {}).get("emi_emc", {}).get("return_via_radius"),
            "emi_emc_max_loop_length": config.get("rules", {}).get("emi_emc", {}).get("max_loop_length"),
            "stackup_return_path_max_signal_layers": config.get("rules", {}).get("stackup_return_path", {}).get("max_signal_layers"),
            "stackup_return_path_signal_via_ground_radius": config.get("rules", {}).get("stackup_return_path", {}).get("signal_via_ground_radius"),
            "stackup_return_path_max_two_layer_critical_length": config.get("rules", {}).get("stackup_return_path", {}).get("max_two_layer_critical_length"),
            "assembly_testability_min_fiducials": config.get("rules", {}).get("assembly_testability", {}).get("min_fiducials"),
            "assembly_testability_probe_access_radius": config.get("rules", {}).get("assembly_testability", {}).get("probe_access_radius"),
            "assembly_testability_min_ground_test_points": config.get("rules", {}).get("assembly_testability", {}).get("min_ground_test_points"),
            "safety_high_voltage_min_clearance": config.get("rules", {}).get("safety_high_voltage", {}).get("min_clearance"),
            "safety_high_voltage_min_creepage": config.get("rules", {}).get("safety_high_voltage", {}).get("min_creepage"),
            "safety_high_voltage_net_keywords": config.get("rules", {}).get("safety_high_voltage", {}).get("high_voltage_net_keywords", []),
            "power_path_realism_neckdown_ratio_threshold": config.get("rules", {}).get("power_path_realism", {}).get("neckdown_ratio_threshold"),
            "power_path_realism_max_high_current_length": config.get("rules", {}).get("power_path_realism", {}).get("max_high_current_length"),
            "power_path_realism_converter_cap_radius": config.get("rules", {}).get("power_path_realism", {}).get("converter_cap_radius"),
            "power_path_realism_max_high_current_vias": config.get("rules", {}).get("power_path_realism", {}).get("max_high_current_vias"),
        },
    }


def _get_first_present(form_data, keys, default=""):
    for key in keys:
        if key in form_data:
            return str(form_data.get(key, "")).strip()
    return default


def _sanitize_list(values):
    cleaned = []
    seen = set()

    for value in values:
        item = str(value).strip()
        if not item:
            continue
        if item in seen:
            continue
        cleaned.append(item)
        seen.add(item)

    return cleaned


def _parse_float(raw_value, fallback):
    if raw_value == "":
        return fallback
    return float(raw_value)


def _parse_int(raw_value, fallback):
    if raw_value == "":
        return fallback
    return int(raw_value)


def _parse_list(raw_value, fallback):
    if raw_value == "":
        return fallback
    return _sanitize_list(raw_value.split(","))


def _parse_bool(raw_value, fallback):
    if raw_value == "":
        return fallback
    return str(raw_value).strip().lower() in {"true", "1", "yes", "on", "enabled"}


def _parse_string(raw_value, fallback):
    if raw_value == "":
        return fallback
    return str(raw_value).strip()


def _ensure_rule_sections(config):
    config.setdefault("analysis", {})
    config["analysis"].setdefault("category_toggles", {})
    config["analysis"].setdefault("rule_toggles", {})
    config.setdefault("rules", {})
    config["rules"].setdefault("spacing", {})
    config["rules"].setdefault("density", {})
    config["rules"].setdefault("signal_path", {})
    config["rules"].setdefault("net_length", {})
    config["rules"].setdefault("trace_quality", {})
    config["rules"].setdefault("power_connectivity", {})
    config["rules"].setdefault("power_distribution", {})
    config["rules"].setdefault("power_rail", {})
    config["rules"].setdefault("decoupling", {})
    config["rules"].setdefault("thermal", {})
    config["rules"].setdefault("ground_reference", {})
    config["rules"].setdefault("return_path", {})
    config["rules"].setdefault("signal_integrity_advanced", {})
    config["rules"].setdefault("differential_pair", {})
    config["rules"].setdefault("manufacturability", {})
    config["rules"].setdefault("thermal_management", {})
    config["rules"].setdefault("reliability", {})
    config["rules"].setdefault("component_analysis", {})
    config["rules"].setdefault("clock_sensitive_placement", {})
    config["rules"].setdefault("emi_emc", {})
    config["rules"].setdefault("stackup_return_path", {})
    config["rules"].setdefault("assembly_testability", {})
    config["rules"].setdefault("safety_high_voltage", {})
    config["rules"].setdefault("power_path_realism", {})


def _apply_rule_mirrors(config):
    _ensure_rule_sections(config)

    for section_name, fields in EDITABLE_FIELD_MAP.items():
        for field_name, metadata in fields.items():
            config_path = metadata.get("config_path")
            if config_path:
                value = config.get(section_name, {})
                for key in config_path:
                    if not isinstance(value, dict):
                        value = None
                        break
                    value = value.get(key)
            else:
                value = config.get(section_name, {}).get(field_name)

            for rule_name, rule_field in metadata.get("rules_targets", []):
                config["rules"].setdefault(rule_name, {})
                config["rules"][rule_name][rule_field] = deepcopy(value)


def validate_config(config):
    errors = []

    analysis = config.get("analysis", {})
    layout = config.get("layout", {})
    power = config.get("power", {})
    signal = config.get("signal", {})

    min_spacing = layout.get("min_component_spacing")
    density_threshold = layout.get("density_threshold")
    density_region_size = layout.get("density_region_size")
    max_trace_length = signal.get("max_trace_length")
    required_power_nets = power.get("required_power_nets", [])
    required_ground_nets = power.get("required_ground_nets", [])
    critical_nets = signal.get("critical_nets", [])
    min_general_trace_width = signal.get("min_general_trace_width")
    distribution_distance_threshold = power.get("distribution_distance_threshold")
    decoupling_distance_threshold = power.get("decoupling_distance_threshold")
    power_max_trace_length = power.get("max_trace_length")
    power_min_trace_width = power.get("min_trace_width")
    power_max_via_count = power.get("max_via_count")
    power_min_connections = power.get("min_connections")
    hotspot_distance_threshold = config.get("thermal", {}).get("hotspot_distance_threshold")
    severity_penalties = config.get("score", {}).get("severity_penalties", {})
    profile = analysis.get("profile", "balanced")
    board_type = analysis.get("board_type", "general")

    if profile not in SUPPORTED_ANALYSIS_PROFILES:
        errors.append("analysis.profile must be a supported preset or custom profile.")

    if not isinstance(board_type, str) or not board_type.strip():
        errors.append("analysis.board_type must be a non-empty string.")

    if not isinstance(min_spacing, (int, float)) or min_spacing <= 0:
        errors.append("layout.min_component_spacing must be a positive number.")

    if not isinstance(density_threshold, int) or density_threshold <= 0:
        errors.append("layout.density_threshold must be a positive integer.")

    if not isinstance(density_region_size, (int, float)) or density_region_size <= 0:
        errors.append("layout.density_region_size must be a positive number.")

    if not isinstance(max_trace_length, (int, float)) or max_trace_length <= 0:
        errors.append("signal.max_trace_length must be a positive number.")

    if not isinstance(min_general_trace_width, (int, float)) or min_general_trace_width <= 0:
        errors.append("signal.min_general_trace_width must be a positive number.")

    if not isinstance(required_power_nets, list) or not required_power_nets:
        errors.append("power.required_power_nets must contain at least one net.")

    if not isinstance(required_ground_nets, list) or not required_ground_nets:
        errors.append("power.required_ground_nets must contain at least one net.")

    if not isinstance(critical_nets, list):
        errors.append("signal.critical_nets must be a list.")

    if not isinstance(distribution_distance_threshold, (int, float)) or distribution_distance_threshold <= 0:
        errors.append("power.distribution_distance_threshold must be a positive number.")

    if not isinstance(decoupling_distance_threshold, (int, float)) or decoupling_distance_threshold <= 0:
        errors.append("power.decoupling_distance_threshold must be a positive number.")

    if not isinstance(power_max_trace_length, (int, float)) or power_max_trace_length <= 0:
        errors.append("power.max_trace_length must be a positive number.")

    if not isinstance(power_min_trace_width, (int, float)) or power_min_trace_width <= 0:
        errors.append("power.min_trace_width must be a positive number.")

    if not isinstance(power_max_via_count, int) or power_max_via_count < 0:
        errors.append("power.max_via_count must be a non-negative integer.")

    if not isinstance(power_min_connections, int) or power_min_connections <= 0:
        errors.append("power.min_connections must be a positive integer.")

    if not isinstance(hotspot_distance_threshold, (int, float)) or hotspot_distance_threshold <= 0:
        errors.append("thermal.hotspot_distance_threshold must be a positive number.")

    for severity in ["low", "medium", "high", "critical"]:
        penalty = severity_penalties.get(severity)
        if not isinstance(penalty, (int, float)) or penalty < 0:
            errors.append(f"score.severity_penalties.{severity} must be a non-negative number.")

    return errors


def build_sanitized_config(config):
    merged = _deep_merge(DEFAULT_CONFIG, config)

    merged.setdefault("analysis", {})
    merged.setdefault("layout", {})
    merged.setdefault("power", {})
    merged.setdefault("signal", {})
    merged.setdefault("thermal", {})
    merged.setdefault("emi", {})
    merged.setdefault("score", {})
    merged["score"].setdefault("severity_penalties", {})
    merged.setdefault("rules", {})

    merged["analysis"]["profile"] = str(
        merged["analysis"].get("profile", DEFAULT_CONFIG["analysis"]["profile"])
    ).strip() or DEFAULT_CONFIG["analysis"]["profile"]
    if merged["analysis"]["profile"] not in SUPPORTED_ANALYSIS_PROFILES:
        merged["analysis"]["profile"] = DEFAULT_CONFIG["analysis"]["profile"]
    merged["analysis"]["custom_profile_name"] = str(
        merged["analysis"].get("custom_profile_name", DEFAULT_CONFIG["analysis"]["custom_profile_name"])
    ).strip() or DEFAULT_CONFIG["analysis"]["custom_profile_name"]

    merged["analysis"]["board_type"] = str(
        merged["analysis"].get("board_type", DEFAULT_CONFIG["analysis"]["board_type"])
    ).strip() or DEFAULT_CONFIG["analysis"]["board_type"]
    merged["analysis"]["category_toggles"] = deepcopy(
        _deep_merge(
            DEFAULT_CONFIG["analysis"]["category_toggles"],
            merged["analysis"].get("category_toggles", {}),
        )
    )
    merged["analysis"]["rule_toggles"] = deepcopy(merged["analysis"].get("rule_toggles", {}))
    for key, value in list(merged["analysis"]["category_toggles"].items()):
        merged["analysis"]["category_toggles"][key] = bool(value)
    for key, value in list(merged["analysis"]["rule_toggles"].items()):
        merged["analysis"]["rule_toggles"][key] = bool(value)

    merged["layout"]["min_component_spacing"] = float(
        merged["layout"].get("min_component_spacing", DEFAULT_CONFIG["layout"]["min_component_spacing"])
    )
    merged["layout"]["density_threshold"] = int(
        merged["layout"].get("density_threshold", DEFAULT_CONFIG["layout"]["density_threshold"])
    )
    merged["layout"]["density_region_size"] = float(
        merged["layout"].get("density_region_size", DEFAULT_CONFIG["layout"]["density_region_size"])
    )

    merged["power"]["required_power_nets"] = _sanitize_list(
        merged["power"].get("required_power_nets", DEFAULT_CONFIG["power"]["required_power_nets"])
    )
    merged["power"]["required_ground_nets"] = _sanitize_list(
        merged["power"].get("required_ground_nets", DEFAULT_CONFIG["power"]["required_ground_nets"])
    )
    merged["power"]["distribution_distance_threshold"] = float(
        merged["power"].get("distribution_distance_threshold", DEFAULT_CONFIG["power"]["distribution_distance_threshold"])
    )
    merged["power"]["decoupling_distance_threshold"] = float(
        merged["power"].get("decoupling_distance_threshold", DEFAULT_CONFIG["power"]["decoupling_distance_threshold"])
    )
    merged["power"]["max_trace_length"] = float(
        merged["power"].get("max_trace_length", DEFAULT_CONFIG["power"]["max_trace_length"])
    )
    merged["power"]["min_trace_width"] = float(
        merged["power"].get("min_trace_width", DEFAULT_CONFIG["power"]["min_trace_width"])
    )
    merged["power"]["max_via_count"] = int(
        merged["power"].get("max_via_count", DEFAULT_CONFIG["power"]["max_via_count"])
    )
    merged["power"]["min_connections"] = int(
        merged["power"].get("min_connections", DEFAULT_CONFIG["power"]["min_connections"])
    )

    merged["signal"]["max_trace_length"] = float(
        merged["signal"].get("max_trace_length", DEFAULT_CONFIG["signal"]["max_trace_length"])
    )
    merged["signal"]["critical_nets"] = _sanitize_list(
        merged["signal"].get("critical_nets", DEFAULT_CONFIG["signal"]["critical_nets"])
    )
    merged["signal"]["min_general_trace_width"] = float(
        merged["signal"].get("min_general_trace_width", DEFAULT_CONFIG["signal"]["min_general_trace_width"])
    )
    merged["signal"]["excluded_net_keywords"] = _sanitize_list(
        merged["signal"].get("excluded_net_keywords", DEFAULT_CONFIG["signal"]["excluded_net_keywords"])
    )
    merged["thermal"]["hotspot_distance_threshold"] = float(
        merged["thermal"].get("hotspot_distance_threshold", DEFAULT_CONFIG["thermal"]["hotspot_distance_threshold"])
    )
    merged["emi"]["require_ground_reference"] = bool(
        merged["emi"].get("require_ground_reference", DEFAULT_CONFIG["emi"]["require_ground_reference"])
    )

    for severity in ["low", "medium", "high", "critical"]:
        merged["score"]["severity_penalties"][severity] = float(
            merged["score"]["severity_penalties"].get(
                severity,
                DEFAULT_CONFIG["score"]["severity_penalties"][severity],
            )
        )

    _ensure_rule_sections(merged)
    merged["rules"]["signal_integrity_advanced"]["max_signal_vias"] = int(
        merged["rules"]["signal_integrity_advanced"].get("max_signal_vias", DEFAULT_CONFIG["rules"]["signal_integrity_advanced"]["max_signal_vias"])
    )
    merged["rules"]["signal_integrity_advanced"]["width_ratio_threshold"] = float(
        merged["rules"]["signal_integrity_advanced"].get("width_ratio_threshold", DEFAULT_CONFIG["rules"]["signal_integrity_advanced"]["width_ratio_threshold"])
    )
    merged["rules"]["signal_integrity_advanced"]["detour_ratio_threshold"] = float(
        merged["rules"]["signal_integrity_advanced"].get("detour_ratio_threshold", DEFAULT_CONFIG["rules"]["signal_integrity_advanced"]["detour_ratio_threshold"])
    )
    merged["rules"]["signal_integrity_advanced"]["stub_length_threshold"] = float(
        merged["rules"]["signal_integrity_advanced"].get("stub_length_threshold", DEFAULT_CONFIG["rules"]["signal_integrity_advanced"]["stub_length_threshold"])
    )
    merged["rules"]["signal_integrity_advanced"]["crosstalk_spacing_threshold"] = float(
        merged["rules"]["signal_integrity_advanced"].get("crosstalk_spacing_threshold", DEFAULT_CONFIG["rules"]["signal_integrity_advanced"]["crosstalk_spacing_threshold"])
    )
    merged["rules"]["differential_pair"]["length_mismatch_threshold"] = float(
        merged["rules"]["differential_pair"].get("length_mismatch_threshold", DEFAULT_CONFIG["rules"]["differential_pair"]["length_mismatch_threshold"])
    )
    merged["rules"]["differential_pair"]["via_mismatch_threshold"] = int(
        merged["rules"]["differential_pair"].get("via_mismatch_threshold", DEFAULT_CONFIG["rules"]["differential_pair"]["via_mismatch_threshold"])
    )
    merged["rules"]["manufacturability"]["min_drill"] = float(
        merged["rules"]["manufacturability"].get("min_drill", DEFAULT_CONFIG["rules"]["manufacturability"]["min_drill"])
    )
    merged["rules"]["manufacturability"]["min_annular_ring"] = float(
        merged["rules"]["manufacturability"].get("min_annular_ring", DEFAULT_CONFIG["rules"]["manufacturability"]["min_annular_ring"])
    )
    merged["rules"]["manufacturability"]["via_in_pad_distance"] = float(
        merged["rules"]["manufacturability"].get("via_in_pad_distance", DEFAULT_CONFIG["rules"]["manufacturability"]["via_in_pad_distance"])
    )
    merged["rules"]["thermal_management"]["min_thermal_vias"] = int(
        merged["rules"]["thermal_management"].get("min_thermal_vias", DEFAULT_CONFIG["rules"]["thermal_management"]["min_thermal_vias"])
    )
    merged["rules"]["thermal_management"]["thermal_via_radius"] = float(
        merged["rules"]["thermal_management"].get("thermal_via_radius", DEFAULT_CONFIG["rules"]["thermal_management"]["thermal_via_radius"])
    )
    merged["rules"]["thermal_management"]["min_heat_spread_width"] = float(
        merged["rules"]["thermal_management"].get("min_heat_spread_width", DEFAULT_CONFIG["rules"]["thermal_management"]["min_heat_spread_width"])
    )
    merged["rules"]["reliability"]["min_ground_vias"] = int(
        merged["rules"]["reliability"].get("min_ground_vias", DEFAULT_CONFIG["rules"]["reliability"]["min_ground_vias"])
    )
    merged["rules"]["reliability"]["min_ground_connections"] = int(
        merged["rules"]["reliability"].get("min_ground_connections", DEFAULT_CONFIG["rules"]["reliability"]["min_ground_connections"])
    )
    merged["rules"]["component_analysis"]["termination_length_threshold"] = float(
        merged["rules"]["component_analysis"].get("termination_length_threshold", DEFAULT_CONFIG["rules"]["component_analysis"]["termination_length_threshold"])
    )
    merged["rules"]["clock_sensitive_placement"]["max_clock_source_distance"] = float(
        merged["rules"]["clock_sensitive_placement"].get("max_clock_source_distance", DEFAULT_CONFIG["rules"]["clock_sensitive_placement"]["max_clock_source_distance"])
    )
    merged["rules"]["clock_sensitive_placement"]["sensitive_aggressor_keepout"] = float(
        merged["rules"]["clock_sensitive_placement"].get("sensitive_aggressor_keepout", DEFAULT_CONFIG["rules"]["clock_sensitive_placement"]["sensitive_aggressor_keepout"])
    )
    merged["rules"]["emi_emc"]["max_switch_trace_length"] = float(
        merged["rules"]["emi_emc"].get("max_switch_trace_length", DEFAULT_CONFIG["rules"]["emi_emc"]["max_switch_trace_length"])
    )
    merged["rules"]["emi_emc"]["sensitive_keepout"] = float(
        merged["rules"]["emi_emc"].get("sensitive_keepout", DEFAULT_CONFIG["rules"]["emi_emc"]["sensitive_keepout"])
    )
    merged["rules"]["emi_emc"]["return_via_radius"] = float(
        merged["rules"]["emi_emc"].get("return_via_radius", DEFAULT_CONFIG["rules"]["emi_emc"]["return_via_radius"])
    )
    merged["rules"]["emi_emc"]["max_loop_length"] = float(
        merged["rules"]["emi_emc"].get("max_loop_length", DEFAULT_CONFIG["rules"]["emi_emc"]["max_loop_length"])
    )
    merged["rules"]["stackup_return_path"]["max_signal_layers"] = int(
        merged["rules"]["stackup_return_path"].get("max_signal_layers", DEFAULT_CONFIG["rules"]["stackup_return_path"]["max_signal_layers"])
    )
    merged["rules"]["stackup_return_path"]["signal_via_ground_radius"] = float(
        merged["rules"]["stackup_return_path"].get("signal_via_ground_radius", DEFAULT_CONFIG["rules"]["stackup_return_path"]["signal_via_ground_radius"])
    )
    merged["rules"]["stackup_return_path"]["max_two_layer_critical_length"] = float(
        merged["rules"]["stackup_return_path"].get("max_two_layer_critical_length", DEFAULT_CONFIG["rules"]["stackup_return_path"]["max_two_layer_critical_length"])
    )
    merged["rules"]["assembly_testability"]["min_fiducials"] = int(
        merged["rules"]["assembly_testability"].get("min_fiducials", DEFAULT_CONFIG["rules"]["assembly_testability"]["min_fiducials"])
    )
    merged["rules"]["assembly_testability"]["probe_access_radius"] = float(
        merged["rules"]["assembly_testability"].get("probe_access_radius", DEFAULT_CONFIG["rules"]["assembly_testability"]["probe_access_radius"])
    )
    merged["rules"]["assembly_testability"]["min_ground_test_points"] = int(
        merged["rules"]["assembly_testability"].get("min_ground_test_points", DEFAULT_CONFIG["rules"]["assembly_testability"]["min_ground_test_points"])
    )
    merged["rules"]["safety_high_voltage"]["min_clearance"] = float(
        merged["rules"]["safety_high_voltage"].get("min_clearance", DEFAULT_CONFIG["rules"]["safety_high_voltage"]["min_clearance"])
    )
    merged["rules"]["safety_high_voltage"]["min_creepage"] = float(
        merged["rules"]["safety_high_voltage"].get("min_creepage", DEFAULT_CONFIG["rules"]["safety_high_voltage"]["min_creepage"])
    )
    merged["rules"]["safety_high_voltage"]["high_voltage_net_keywords"] = _sanitize_list(
        merged["rules"]["safety_high_voltage"].get("high_voltage_net_keywords", DEFAULT_CONFIG["rules"]["safety_high_voltage"]["high_voltage_net_keywords"])
    )
    merged["rules"]["power_path_realism"]["neckdown_ratio_threshold"] = float(
        merged["rules"]["power_path_realism"].get("neckdown_ratio_threshold", DEFAULT_CONFIG["rules"]["power_path_realism"]["neckdown_ratio_threshold"])
    )
    merged["rules"]["power_path_realism"]["max_high_current_length"] = float(
        merged["rules"]["power_path_realism"].get("max_high_current_length", DEFAULT_CONFIG["rules"]["power_path_realism"]["max_high_current_length"])
    )
    merged["rules"]["power_path_realism"]["converter_cap_radius"] = float(
        merged["rules"]["power_path_realism"].get("converter_cap_radius", DEFAULT_CONFIG["rules"]["power_path_realism"]["converter_cap_radius"])
    )
    merged["rules"]["power_path_realism"]["max_high_current_vias"] = int(
        merged["rules"]["power_path_realism"].get("max_high_current_vias", DEFAULT_CONFIG["rules"]["power_path_realism"]["max_high_current_vias"])
    )

    _apply_rule_mirrors(merged)
    return merged


def parse_config_form(form_data, config_path="custom_config.json"):
    current_config = load_config(config_path)
    config = deepcopy(current_config)

    config.setdefault("layout", {})
    config.setdefault("power", {})
    config.setdefault("signal", {})
    config.setdefault("thermal", {})
    config.setdefault("emi", {})
    config.setdefault("score", {})
    config["score"].setdefault("severity_penalties", {})

    for section_name, fields in EDITABLE_FIELD_MAP.items():
        for field_name, metadata in fields.items():
            raw_value = _get_first_present(form_data, metadata["form_keys"], "")
            config_path_keys = metadata.get("config_path")
            if config_path_keys:
                current_value = config.get(section_name, {})
                default_value = DEFAULT_CONFIG.get(section_name, {})
                for key in config_path_keys:
                    if isinstance(current_value, dict):
                        current_value = current_value.get(key)
                    if isinstance(default_value, dict):
                        default_value = default_value.get(key)
                if current_value is None:
                    current_value = default_value
            else:
                current_value = config.get(section_name, {}).get(
                    field_name,
                    DEFAULT_CONFIG.get(section_name, {}).get(field_name),
                )

            if metadata["type"] == "float":
                parsed_value = _parse_float(raw_value, current_value)
            elif metadata["type"] == "int":
                parsed_value = _parse_int(raw_value, current_value)
            elif metadata["type"] == "list":
                parsed_value = _parse_list(raw_value, current_value)
            elif metadata["type"] == "bool":
                parsed_value = _parse_bool(raw_value, current_value)
            elif metadata["type"] == "str":
                parsed_value = _parse_string(raw_value, current_value)
            else:
                parsed_value = current_value

            if config_path_keys:
                target = config[section_name]
                for key in config_path_keys[:-1]:
                    target = target.setdefault(key, {})
                target[config_path_keys[-1]] = parsed_value
            else:
                config[section_name][field_name] = parsed_value

    config = build_sanitized_config(config)

    errors = validate_config(config)
    if errors:
        raise ValueError(" ".join(errors))

    return config


def _deep_merge_in_place(base, overlay):
    for key, value in (overlay or {}).items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge_in_place(base[key], value)
        else:
            base[key] = deepcopy(value)
    return base


def apply_analysis_profile(config, profile_name=None, board_type=None):
    merged = _deep_merge(DEFAULT_CONFIG, config or {})
    analysis = merged.setdefault("analysis", {})
    selected_profile = str(profile_name or analysis.get("profile") or "balanced").strip().lower()
    selected_board_type = str(board_type or analysis.get("board_type") or "general").strip().lower()

    overlays = []
    if selected_board_type in ANALYSIS_PROFILE_PRESETS and selected_board_type != "general":
        overlays.append(ANALYSIS_PROFILE_PRESETS[selected_board_type])
    if selected_profile in ANALYSIS_PROFILE_PRESETS and selected_profile != "balanced":
        overlays.append(ANALYSIS_PROFILE_PRESETS[selected_profile])

    for overlay in overlays:
        _deep_merge_in_place(merged, overlay)

    analysis["profile"] = selected_profile if selected_profile in SUPPORTED_ANALYSIS_PROFILES else "balanced"
    analysis["board_type"] = selected_board_type or "general"
    return build_sanitized_config(merged)
