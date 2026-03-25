from collections import defaultdict


SEVERITY_PENALTIES = {
    "low": 0.5,
    "medium": 1.0,
    "high": 1.5,
    "critical": 2.0,
}


def build_score_explanation(risks, start_score=10.0):
    severity_totals = defaultdict(float)
    category_totals = defaultdict(float)
    detailed_penalties = []

    total_penalty = 0.0

    for risk in risks:
        severity = str(risk.get("severity", "low")).lower()
        category = risk.get("category", "uncategorized")
        message = risk.get("message", "No message provided")
        rule_id = risk.get("rule_id", "UNKNOWN_RULE")

        penalty = SEVERITY_PENALTIES.get(severity, 0.5)

        total_penalty += penalty
        severity_totals[severity] += penalty
        category_totals[category] += penalty

        detailed_penalties.append({
            "rule_id": rule_id,
            "severity": severity,
            "category": category,
            "penalty": penalty,
            "message": message,
            "components": risk.get("components", []),
            "nets": risk.get("nets", []),
        })

    final_score = round(max(0.0, start_score - total_penalty), 2)

    return {
        "start_score": round(start_score, 2),
        "total_penalty": round(total_penalty, 2),
        "final_score": final_score,
        "severity_totals": {
            key: round(value, 2)
            for key, value in sorted(severity_totals.items())
        },
        "category_totals": {
            key: round(value, 2)
            for key, value in sorted(category_totals.items())
        },
        "detailed_penalties": detailed_penalties,
    }