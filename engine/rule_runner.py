import importlib
import os


def calculate_risk_score(risks):
    score = 10.0

    severity_penalties = {
        "low": 0.5,
        "medium": 1.0,
        "high": 1.5,
        "critical": 2.0,
    }

    for risk in risks:
        severity = risk.get("severity", "medium")
        score -= severity_penalties.get(severity, 1.0)

    if score < 0:
        score = 0

    return round(score, 2)


def load_rule_functions():
    rule_functions = []
    rules_dir = os.path.join(os.path.dirname(__file__), "rules")

    for filename in os.listdir(rules_dir):
        if filename.endswith(".py") and filename not in {"__init__.py"}:
            module_name = filename[:-3]
            module = importlib.import_module(f"engine.rules.{module_name}")

            if hasattr(module, "run_rule"):
                rule_functions.append(module.run_rule)

    return rule_functions


def run_analysis(pcb):
    risks = []

    rule_functions = load_rule_functions()

    for rule_function in rule_functions:
        rule_risks = rule_function(pcb)
        if rule_risks:
            risks.extend(rule_risks)

    score = calculate_risk_score(risks)
    return risks, score