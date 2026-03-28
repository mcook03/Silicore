from collections import defaultdict

DEFAULT_SEVERITY_PENALTIES = {
    "low": 0.5,
    "medium": 1.0,
    "high": 1.5,
    "critical": 2.0,
}


def get_severity_penalties(config=None):
    penalties = DEFAULT_SEVERITY_PENALTIES.copy()

    if not isinstance(config, dict):
        return penalties

    configured = config.get("score", {}).get("severity_penalties", {})
    if not isinstance(configured, dict):
        return penalties

    for severity, value in configured.items():
        key = str(severity).lower()
        try:
            penalties[key] = float(value)
        except (TypeError, ValueError):
            continue

    return penalties


def build_score_explanation(risks, config=None, start_score=10.0):
    severity_penalties = get_severity_penalties(config)

    severity_totals = defaultdict(float)
    category_totals = defaultdict(float)
    detailed_penalties = []
    total_penalty = 0.0

    for risk in risks or []:
        severity = str(risk.get("severity", "low")).lower()
        category = risk.get("category", "uncategorized")
        message = risk.get("message", "No message provided")
        rule_id = risk.get("rule_id", "UNKNOWN_RULE")

        penalty = float(severity_penalties.get(severity, 0.0))

        severity_totals[severity] += penalty
        category_totals[category] += penalty
        total_penalty += penalty

        detailed_penalties.append(
            {
                "rule_id": rule_id,
                "severity": severity,
                "category": category,
                "message": message,
                "penalty": penalty,
            }
        )

    final_score = max(round(float(start_score) - total_penalty, 2), 0.0)

    explanation = {
        "start_score": float(start_score),
        "total_penalty": round(total_penalty, 2),
        "final_score": final_score,
        "severity_totals": dict(sorted(severity_totals.items())),
        "category_totals": dict(sorted(category_totals.items())),
        "detailed_penalties": detailed_penalties,
    }

    return final_score, explanation