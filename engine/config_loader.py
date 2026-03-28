import json
import os
from copy import deepcopy

from engine.config import DEFAULT_CONFIG


def _deep_merge(base, override):
    result = deepcopy(base)

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
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
            "density_threshold": config["layout"]["density_threshold"],
        },
        "power": {
            "required_power_nets": config["power"]["required_power_nets"],
            "required_ground_nets": config["power"]["required_ground_nets"],
        },
        "signal": {
            "max_trace_length": config["signal"]["max_trace_length"],
            "critical_nets": config["signal"]["critical_nets"],
        },
    }


def _get_first_present(form_data, keys, default=""):
    for key in keys:
        if key in form_data:
            return str(form_data.get(key, "")).strip()
    return default


def parse_config_form(form_data, config_path="custom_config.json"):
    current_config = load_config(config_path)
    config = deepcopy(current_config)

    def parse_float(keys, current_value):
        raw = _get_first_present(form_data, keys, "")
        if raw == "":
            return current_value
        return float(raw)

    def parse_int(keys, current_value):
        raw = _get_first_present(form_data, keys, "")
        if raw == "":
            return current_value
        return int(raw)

    def parse_list(keys, current_value):
        raw = _get_first_present(form_data, keys, "")
        if raw == "":
            return current_value
        return [item.strip() for item in raw.split(",") if item.strip()]

    config["layout"]["min_component_spacing"] = parse_float(
        ["layout_min_component_spacing", "min_component_spacing"],
        config["layout"]["min_component_spacing"],
    )

    config["layout"]["density_threshold"] = parse_int(
        ["layout_density_threshold", "density_threshold"],
        config["layout"]["density_threshold"],
    )

    config["power"]["required_power_nets"] = parse_list(
        ["power_required_power_nets", "required_power_nets"],
        config["power"]["required_power_nets"],
    )

    config["power"]["required_ground_nets"] = parse_list(
        ["power_required_ground_nets", "required_ground_nets"],
        config["power"]["required_ground_nets"],
    )

    config["signal"]["max_trace_length"] = parse_float(
        ["signal_max_trace_length", "max_trace_length"],
        config["signal"]["max_trace_length"],
    )

    config["signal"]["critical_nets"] = parse_list(
        ["signal_critical_nets", "critical_nets"],
        config["signal"]["critical_nets"],
    )

    if "rules" not in config:
        config["rules"] = {}

    if "spacing" not in config["rules"]:
        config["rules"]["spacing"] = {}
    config["rules"]["spacing"]["threshold"] = config["layout"]["min_component_spacing"]

    if "density" not in config["rules"]:
        config["rules"]["density"] = {}
    config["rules"]["density"]["component_threshold"] = config["layout"]["density_threshold"]

    if "signal_path" not in config["rules"]:
        config["rules"]["signal_path"] = {}
    config["rules"]["signal_path"]["threshold"] = config["signal"]["max_trace_length"]

    if "net_length" not in config["rules"]:
        config["rules"]["net_length"] = {}
    config["rules"]["net_length"]["max_trace_length"] = config["signal"]["max_trace_length"]
    config["rules"]["net_length"]["critical_nets"] = config["signal"]["critical_nets"]

    if "power_connectivity" not in config["rules"]:
        config["rules"]["power_connectivity"] = {}
    config["rules"]["power_connectivity"]["required_power_nets"] = config["power"]["required_power_nets"]
    config["rules"]["power_connectivity"]["required_ground_nets"] = config["power"]["required_ground_nets"]

    return config