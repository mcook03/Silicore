def normalize_text(text):
    return str(text or "").lower().strip()


def normalize_message(msg):
    msg = normalize_text(msg)
    for token in ["warning:", "issue:", "risk:"]:
        msg = msg.replace(token, "")
    return " ".join(msg.split())


def build_signature(risk):
    category = normalize_text(risk.get("category"))
    rule_id = normalize_text(risk.get("rule_id"))
    message = normalize_message(risk.get("message"))

    components = sorted(risk.get("components", []) or [])
    nets = sorted(risk.get("nets", []) or [])

    base_signature = f"{category}|{rule_id}|{message}"
    full_signature = f"{base_signature}|c:{','.join(components)}|n:{','.join(nets)}"

    return full_signature


def make_risk_key(risk):
    # 🔥 upgraded: fallback to advanced signature
    return (
        risk.get("rule_id"),
        tuple(sorted(risk.get("components", []))),
        tuple(sorted(risk.get("nets", []))),
        risk.get("region"),
        normalize_message(risk.get("short_title") or risk.get("message")),
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

    if "trace_length" in old_m and "trace_length" in new_m:
        old_t = old_m["trace_length"]
        new_t = new_m["trace_length"]

        if new_t < old_t:
            return f"Improved: trace length decreased from {old_t} to {new_t}"
        elif new_t > old_t:
            return f"Worsened: trace length increased from {old_t} to {new_t}"

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

    # 🔥 NEW: smarter summary
    report.append("REVISION COMPARISON")
    report.append("=" * 40)
    report.append("")
    report.append("SUMMARY")
    report.append("-" * 40)
    report.append(f"Old Score: {old_score}")
    report.append(f"New Score: {new_score}")
    report.append(f"Score Change: {new_score - old_score:+.2f}")
    report.append(f"Resolved Risks: {len(resolved)}")
    report.append(f"New Risks: {len(new_only)}")
    report.append(f"Improved Persisting Risks: {len(improved)}")
    report.append(f"Worsened Persisting Risks: {len(worsened)}")
    report.append(f"Unchanged Persisting Risks: {len(unchanged)}")
    report.append("")

    if new_score > old_score:
        report.append("Overall: Design improved.")
    elif new_score < old_score:
        report.append("Overall: Design regressed.")
    else:
        report.append("Overall: No score change.")
    report.append("")

    # rest unchanged
    report.append("RESOLVED RISKS")
    report.append("-" * 40)
    report.extend([f"- {old_map[k]['message']}" for k in resolved] or ["None"])
    report.append("")

    report.append("NEW RISKS")
    report.append("-" * 40)
    report.extend([f"- {new_map[k]['message']}" for k in new_only] or ["None"])
    report.append("")

    report.append("IMPROVED PERSISTING RISKS")
    report.append("-" * 40)
    if improved:
        for item in improved:
            report.append(f"- {item['message']}")
            report.append(f"  {item['trend']}")
    else:
        report.append("None")
    report.append("")

    report.append("WORSENED PERSISTING RISKS")
    report.append("-" * 40)
    if worsened:
        for item in worsened:
            report.append(f"- {item['message']}")
            report.append(f"  {item['trend']}")
    else:
        report.append("None")
    report.append("")

    return "\n".join(report)