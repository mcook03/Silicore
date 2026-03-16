def make_risk(
    rule_id,
    category,
    severity,
    message,
    recommendation="",
    components=None,
    nets=None,
    region=None,
):
    return {
        "rule_id": rule_id,
        "category": category,
        "severity": severity,
        "message": message,
        "recommendation": recommendation,
        "components": components or [],
        "nets": nets or [],
        "region": region,
    }