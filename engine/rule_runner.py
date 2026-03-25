import importlib
import os

from engine.score_explainer import build_score_explanation


RULES_PACKAGE = "engine.rules"
RULES_DIRECTORY = os.path.join(os.path.dirname(__file__), "rules")


def load_rule_modules():
    rule_modules = []

    for filename in os.listdir(RULES_DIRECTORY):
        if not filename.endswith(".py"):
            continue
        if filename == "__init__.py":
            continue

        module_name = filename[:-3]
        full_module_name = f"{RULES_PACKAGE}.{module_name}"
        module = importlib.import_module(full_module_name)

        if hasattr(module, "run_rule"):
            rule_modules.append(module)

    return rule_modules


def run_analysis(pcb, config, debug=False):
    risks = []
    loaded_rules = load_rule_modules()

    for rule_module in loaded_rules:
        try:
            rule_risks = rule_module.run_rule(pcb, config)
            if rule_risks:
                risks.extend(rule_risks)
        except Exception as exc:
            if debug:
                print(f"Rule error in {rule_module.__name__}: {exc}")

    score_explanation = build_score_explanation(risks, start_score=10.0)

    severity_counts = {
        "low": 0,
        "medium": 0,
        "high": 0,
        "critical": 0,
    }

    category_counts = {}

    for risk in risks:
        severity = str(risk.get("severity", "low")).lower()
        category = risk.get("category", "uncategorized")

        if severity in severity_counts:
            severity_counts[severity] += 1
        else:
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        category_counts[category] = category_counts.get(category, 0) + 1

    return {
        "risks": risks,
        "score": score_explanation["final_score"],
        "score_explanation": score_explanation,
        "risk_summary": {
            "total_risks": len(risks),
            "by_severity": severity_counts,
            "by_category": category_counts,
        },
    }