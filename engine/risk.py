def make_risk(rule_id, severity, message, components=None, nets=None, region=None):
    return {
        "rule_id": rule_id,
        "severity": severity,
        "message": message,
        "components": components or [],
        "nets": nets or [],
        "region": region,
    }
