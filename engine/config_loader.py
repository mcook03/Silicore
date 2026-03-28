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
        },
        "power": {
            "required_power_nets": config.get("power", {}).get("required_power_nets", []),
            "required_ground_nets": config.get("power", {}).get("required_ground_nets", []),
        },
        "signal": {
            "max_trace_length": config.get("signal", {}).get("max_trace_length"),
            "critical_nets": config.get("signal", {}).get("critical_nets", []),
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


def _ensure_rule_sections(config):
    config.setdefault("rules", {})
    config["rules"].setdefault("spacing", {})
    config["rules"].setdefault("density", {})
    config["rules"].setdefault("signal_path", {})
    config["rules"].setdefault("net_length", {})
    config["rules"].setdefault("power_connectivity", {})
    config["rules"].setdefault("ground_reference", {})
    config["rules"].setdefault("return_path", {})


def _apply_rule_mirrors(config):
    _ensure_rule_sections(config)

    for section_name, fields in EDITABLE_FIELD_MAP.items():
        for field_name, metadata in fields.items():
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
    max_trace_length = signal.get("max_trace_length")
    required_power_nets = power.get("required_power_nets", [])
    required_ground_nets = power.get("required_ground_nets", [])
    critical_nets = signal.get("critical_nets", [])

    if not isinstance(min_spacing, (int, float)) or min_spacing <= 0:
        errors.append("layout.min_component_spacing must be a positive number.")

    if not isinstance(density_threshold, int) or density_threshold <= 0:
        errors.append("layout.density_threshold must be a positive integer.")

    if not isinstance(max_trace_length, (int, float)) or max_trace_length <= 0:
        errors.append("signal.max_trace_length must be a positive number.")

    if not isinstance(required_power_nets, list) or not required_power_nets:
        errors.append("power.required_power_nets must contain at least one net.")

    if not isinstance(required_ground_nets, list) or not required_ground_nets:
        errors.append("power.required_ground_nets must contain at least one net.")

    if not isinstance(critical_nets, list):
        errors.append("signal.critical_nets must be a list.")

    return errors


def build_sanitized_config(config):
    merged = _deep_merge(DEFAULT_CONFIG, config)

    merged.setdefault("layout", {})
    merged.setdefault("power", {})
    merged.setdefault("signal", {})

    merged["layout"]["min_component_spacing"] = float(
        merged["layout"].get("min_component_spacing", DEFAULT_CONFIG["layout"]["min_component_spacing"])
    )
    merged["layout"]["density_threshold"] = int(
        merged["layout"].get("density_threshold", DEFAULT_CONFIG["layout"]["density_threshold"])
    )

    merged["power"]["required_power_nets"] = _sanitize_list(
        merged["power"].get("required_power_nets", DEFAULT_CONFIG["power"]["required_power_nets"])
    )
    merged["power"]["required_ground_nets"] = _sanitize_list(
        merged["power"].get("required_ground_nets", DEFAULT_CONFIG["power"]["required_ground_nets"])
    )

    merged["signal"]["max_trace_length"] = float(
        merged["signal"].get("max_trace_length", DEFAULT_CONFIG["signal"]["max_trace_length"])
    )
    merged["signal"]["critical_nets"] = _sanitize_list(
        merged["signal"].get("critical_nets", DEFAULT_CONFIG["signal"]["critical_nets"])
    )

    _apply_rule_mirrors(merged)
    return merged


def parse_config_form(form_data, config_path="custom_config.json"):
    current_config = load_config(config_path)
    config = deepcopy(current_config)

    config.setdefault("layout", {})
    config.setdefault("power", {})
    config.setdefault("signal", {})

    for section_name, fields in EDITABLE_FIELD_MAP.items():
        for field_name, metadata in fields.items():
            raw_value = _get_first_present(form_data, metadata["form_keys"], "")
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
            else:
                parsed_value = current_value

            config[section_name][field_name] = parsed_value

    config = build_sanitized_config(config)

    errors = validate_config(config)
    if errors:
        raise ValueError(" ".join(errors))

    return config