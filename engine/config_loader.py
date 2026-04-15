import json
import os
from copy import deepcopy

from engine.config import DEFAULT_CONFIG


EDITABLE_FIELD_MAP = {
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


def _ensure_rule_sections(config):
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

    merged.setdefault("layout", {})
    merged.setdefault("power", {})
    merged.setdefault("signal", {})
    merged.setdefault("thermal", {})
    merged.setdefault("emi", {})
    merged.setdefault("score", {})
    merged["score"].setdefault("severity_penalties", {})
    merged.setdefault("rules", {})

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
