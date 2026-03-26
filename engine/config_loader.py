import json
import os
from copy import deepcopy
from engine.config import DEFAULT_CONFIG


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
            result[key] = value

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
            "min_component_spacing": config["layout"]["min_component_spacing"],
            "density_threshold": config["layout"]["density_threshold"]
        },
        "power": {
            "required_power_nets": config["power"]["required_power_nets"],
            "required_ground_nets": config["power"]["required_ground_nets"]
        },
        "signal": {
            "max_trace_length": config["signal"]["max_trace_length"],
            "critical_nets": config["signal"]["critical_nets"]
        }
    }


def parse_config_form(form_data):
    def parse_float(name, default_value):
        raw = str(form_data.get(name, "")).strip()
        if raw == "":
            return default_value
        return float(raw)

    def parse_int(name, default_value):
        raw = str(form_data.get(name, "")).strip()
        if raw == "":
            return default_value
        return int(raw)

    def parse_list(name):
        raw = str(form_data.get(name, "")).strip()
        if raw == "":
            return []
        return [item.strip() for item in raw.split(",") if item.strip()]

    config = deepcopy(DEFAULT_CONFIG)

    config["layout"]["min_component_spacing"] = parse_float(
        "min_component_spacing",
        DEFAULT_CONFIG["layout"]["min_component_spacing"]
    )
    config["layout"]["density_threshold"] = parse_int(
        "density_threshold",
        DEFAULT_CONFIG["layout"]["density_threshold"]
    )
    config["signal"]["max_trace_length"] = parse_float(
        "max_trace_length",
        DEFAULT_CONFIG["signal"]["max_trace_length"]
    )
    config["power"]["required_power_nets"] = parse_list("required_power_nets")
    config["power"]["required_ground_nets"] = parse_list("required_ground_nets")
    config["signal"]["critical_nets"] = parse_list("critical_nets")

    return config