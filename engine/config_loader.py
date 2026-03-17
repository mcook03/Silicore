import copy
import json
import os

from engine.config import DEFAULT_CONFIG


def deep_merge_dicts(base, override):
    result = copy.deepcopy(base)

    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def load_config(config_path=None):
    config = copy.deepcopy(DEFAULT_CONFIG)

    if not config_path:
        return config

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        user_config = json.load(f)

    return deep_merge_dicts(config, user_config)