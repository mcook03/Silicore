import importlib
import os

from engine.config import DEFAULT_CONFIG


def load_rule_functions():
    rule_functions = []
    rules_dir = os.path.join(os.path.dirname(__file__), "rules")

    for file in os.listdir(rules_dir):
        if file.endswith(".py") and file != "__init__.py":
            module_name = file[:-3]
            module = importlib.import_module(f"engine.rules.{module_name}")

            if hasattr(module, "run_rule"):
                rule_functions.append((module_name, module.run_rule))

    return rule_functions


def calculate_risk_score(risks, config=None):
    if config is None:
        config = DEFAULT_CONFIG

    scoring = config["scoring"]
    start_score = scoring["start_score"]
    severity_weights = scoring["severity_weights"]
    category_weights = scoring["category_weights"]
    floor = scoring["floor"]
    ceiling = scoring["ceiling"]

    score = start_score
    seen_keys = set()

    for risk in risks:
        severity = risk.get("severity", "medium")
        category = risk.get("category", "other")
        key = (
            risk.get("rule_id"),
            tuple(sorted(risk.get("components", []))),
            tuple(sorted(risk.get("nets", []))),
            risk.get("region"),
        )

        base_penalty = severity_weights.get(severity, 1.0)
        category_multiplier = category_weights.get(category, 1.0)
        penalty = base_penalty * category_multiplier

        if key in seen_keys:
            penalty *= 0.9
        else:
            seen_keys.add(key)

        score -= penalty

    if score < floor:
        score = floor
    if score > ceiling:
        score = ceiling

    return round(score, 2)


def run_analysis(pcb, config=None):
    if config is None:
        config = DEFAULT_CONFIG

    risks = []

    for rule_name, rule_function in load_rule_functions():
        rule_config = config["rules"].get(rule_name, {"enabled": True})
        if not rule_config.get("enabled", True):
            continue

        try:
            result = rule_function(pcb, config)
            if result:
                risks.extend(result)
        except Exception as e:
            risks.append({
                "rule_id": rule_name,
                "category": "other",
                "severity": "low",
                "message": f"Rule execution error in {rule_name}: {e}",
                "recommendation": "Inspect rule implementation.",
                "components": [],
                "nets": [],
                "region": None,
                "metrics": {},
                "confidence": 1.0,
                "short_title": f"{rule_name} execution error",
                "fix_priority": "low",
                "estimated_impact": "low",
                "design_domain": "system",
            })

    score = calculate_risk_score(risks, config)
    return risks, score