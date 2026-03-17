def make_risk_key(risk):
    return (
        risk.get("rule_id"),
        tuple(sorted(risk.get("components", []))),
        tuple(sorted(risk.get("nets", []))),
        risk.get("region"),
    )


def compare_metric_trend(old_risk, new_risk):
    old_m = old_risk.get("metrics", {})
    new_m = new_risk.get("metrics", {})

    if "distance" in old_m and "distance" in new_m:
        old_d = old_m["distance"]
        new_d = new_m["distance"]

        if new_d > old_d:
            return f"Improved: distance increased from {old_d} to {new_d}"
        elif new_d < old_d:
            return f"Worsened: distance decreased from {old_d} to {new_d}"

    if "component_count" in old_m and "component_count" in new_m:
        old_c = old_m["component_count"]
        new_c = new_m["component_count"]

        if new_c < old_c:
            return f"Improved: component count decreased from {old_c} to {new_c}"
        elif new_c > old_c:
            return f"Worsened: component count increased from {old_c} to {new_c}"

    return "Unchanged"


def compare_revisions(old_risks, new_risks, old_score, new_score):
    report = []

    old_map = {make_risk_key(r): r for r in old_risks}
    new_map = {make_risk_key(r): r for r in new_risks}

    old_keys = set(old_map.keys())
    new_keys = set(new_map.keys())

    resolved = old_keys - new_keys
    new_only = new_keys - old_keys
    persisting = old_keys & new_keys

    report.append("REVISION COMPARISON")
    report.append("=" * 40)
    report.append("")
    report.append(f"Old Score: {old_score}")
    report.append(f"New Score: {new_score}")
    report.append(f"Score Change: {new_score - old_score:+.2f}")
    report.append("")

    report.append("RESOLVED RISKS")
    report.append("-" * 40)
    if resolved:
        for key in resolved:
            report.append(f"- {old_map[key]['message']}")
    else:
        report.append("None")
    report.append("")

    report.append("NEW RISKS")
    report.append("-" * 40)
    if new_only:
        for key in new_only:
            report.append(f"- {new_map[key]['message']}")
    else:
        report.append("None")
    report.append("")

    improved = []
    worsened = []
    unchanged = []

    for key in persisting:
        trend = compare_metric_trend(old_map[key], new_map[key])
        item = {
            "message": new_map[key]["message"],
            "previous": old_map[key]["message"],
            "trend": trend,
        }

        if trend.startswith("Improved"):
            improved.append(item)
        elif trend.startswith("Worsened"):
            worsened.append(item)
        else:
            unchanged.append(item)

    report.append("IMPROVED PERSISTING RISKS")
    report.append("-" * 40)
    if improved:
        for item in improved:
            report.append(f"- {item['message']}")
            report.append(f"  Trend: {item['trend']}")
            report.append(f"  Previous: {item['previous']}")
    else:
        report.append("None")
    report.append("")

    report.append("WORSENED PERSISTING RISKS")
    report.append("-" * 40)
    if worsened:
        for item in worsened:
            report.append(f"- {item['message']}")
            report.append(f"  Trend: {item['trend']}")
            report.append(f"  Previous: {item['previous']}")
    else:
        report.append("None")
    report.append("")

    report.append("UNCHANGED PERSISTING RISKS")
    report.append("-" * 40)
    if unchanged:
        for item in unchanged:
            report.append(f"- {item['message']}")
            report.append(f"  Trend: {item['trend']}")
    else:
        report.append("None")
    report.append("")
    report.append("END REVISION COMPARISON")

    return "\n".join(report)