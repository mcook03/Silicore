def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def evaluate_signoff_gate(result):
    result = result or {}
    risks = result.get("risks", []) or []
    score = _safe_float(result.get("score"), 0.0)
    parser_confidence = _safe_float(((result.get("parser_confidence") or {}).get("score")), 0.0)
    physics_summary = result.get("physics_summary") or {}
    score_explanation = result.get("score_explanation") or {}

    critical_count = sum(1 for risk in risks if str((risk or {}).get("severity") or "").lower() == "critical")
    high_count = sum(1 for risk in risks if str((risk or {}).get("severity") or "").lower() == "high")
    traceability_ready = sum(1 for risk in risks if _safe_float(((risk or {}).get("transparency_view") or {}).get("traceability_score"), 0.0) >= 85.0)
    physics_risk_count = len(physics_summary.get("risks") or [])
    worst_ir_drop = _safe_float((physics_summary.get("summary") or {}).get("worst_voltage_drop_mv"), 0.0)
    worst_impedance_mismatch = _safe_float((physics_summary.get("summary") or {}).get("worst_impedance_mismatch_pct"), 0.0)
    overflow_penalty = _safe_float(score_explanation.get("overflow_penalty"), 0.0)

    blockers = []
    if critical_count:
        blockers.append(f"{critical_count} critical finding(s) remain unresolved.")
    if high_count >= 6:
        blockers.append(f"{high_count} high-severity findings still dominate the board.")
    if parser_confidence and parser_confidence < 70:
        blockers.append(f"Parser confidence is only {round(parser_confidence, 1)} / 100.")
    if worst_ir_drop > 75:
        blockers.append(f"Estimated IR drop peaks at {round(worst_ir_drop, 1)} mV.")
    if worst_impedance_mismatch > 20:
        blockers.append(f"Estimated impedance mismatch peaks at {round(worst_impedance_mismatch, 1)}%.")
    if overflow_penalty > 0:
        blockers.append("The score is still in an overflow-penalty regime.")

    release_score = 100.0
    release_score -= min(critical_count * 18, 54)
    release_score -= min(high_count * 4, 24)
    release_score -= min(max(0.0, 75.0 - score), 30.0)
    release_score -= min(max(0.0, 80.0 - parser_confidence) * 0.35, 12.0)
    release_score -= min(physics_risk_count * 4, 16)
    release_score -= min(overflow_penalty * 0.1, 10)
    release_score += min(traceability_ready * 1.5, 8)
    release_score = round(max(0.0, min(100.0, release_score)), 1)

    if blockers:
        decision = "blocked" if critical_count or release_score < 55 else "needs_validation"
    elif release_score >= 80:
        decision = "ready_for_signoff"
    else:
        decision = "validation_pending"

    next_checks = []
    if critical_count:
        next_checks.append("Resolve all critical findings before the next signoff review.")
    if worst_ir_drop > 75:
        next_checks.append("Measure the worst power rail under load and compare against the IR-drop estimate.")
    if worst_impedance_mismatch > 20:
        next_checks.append("Rework the highest-mismatch signal geometry and rerun the impedance estimate.")
    if parser_confidence < 70:
        next_checks.append("Confirm parser assumptions or re-import a richer board source before approval.")
    if not next_checks:
        next_checks.append("Run one validation pass focused on the top fix-first driver, then rerun signoff evaluation.")

    return {
        "decision": decision,
        "release_score": release_score,
        "critical_count": critical_count,
        "high_count": high_count,
        "parser_confidence": round(parser_confidence, 1),
        "physics_risk_count": physics_risk_count,
        "blockers": blockers,
        "next_checks": next_checks[:4],
        "summary": (
            "Board is ready for signoff."
            if decision == "ready_for_signoff"
            else "Board is not yet ready for signoff."
        ),
    }
