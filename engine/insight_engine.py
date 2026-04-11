from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple


SEVERITY_WEIGHTS = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


DEFAULT_CATEGORY = "General"


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _normalize_severity(value: Any) -> str:
    text = _safe_str(value, "low").lower()
    if text in SEVERITY_WEIGHTS:
        return text

    aliases = {
        "minor": "low",
        "moderate": "medium",
        "major": "high",
        "severe": "high",
        "blocker": "critical",
    }
    return aliases.get(text, "low")


def _severity_weight(value: Any) -> int:
    severity = _normalize_severity(value)
    return SEVERITY_WEIGHTS.get(severity, 1)


def _normalize_category(value: Any) -> str:
    text = _safe_str(value, DEFAULT_CATEGORY)
    return text if text else DEFAULT_CATEGORY


def _normalize_message(value: Any) -> str:
    text = _safe_str(value, "")
    return text if text else "Unnamed issue"


def _normalize_recommendation(value: Any) -> str:
    return _safe_str(value, "")


def _normalize_rule_id(value: Any) -> str:
    return _safe_str(value, "")


def _normalize_string_list(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []

    normalized: List[str] = []
    for value in values:
        cleaned = _safe_str(value, "")
        if cleaned:
            normalized.append(cleaned)

    deduped = []
    seen = set()
    for item in normalized:
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        deduped.append(item)

    return deduped


def _format_category_name(value: Any) -> str:
    text = _normalize_category(value)
    return text.replace("_", " ").strip().title()


def _pluralize(word: str, count: int) -> str:
    return word if count == 1 else f"{word}s"


def _risk_identity(risk: Dict[str, Any]) -> Tuple[str, str, str]:
    rule_id = _normalize_rule_id(risk.get("rule_id"))
    category = _normalize_category(risk.get("category"))
    message = _normalize_message(risk.get("message"))

    return (
        rule_id.lower(),
        category.lower(),
        message.lower(),
    )


def _normalize_risk(risk: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "rule_id": _normalize_rule_id(risk.get("rule_id")),
        "category": _normalize_category(risk.get("category")),
        "severity": _normalize_severity(risk.get("severity")),
        "message": _normalize_message(risk.get("message")),
        "recommendation": _normalize_recommendation(risk.get("recommendation")),
        "components": _normalize_string_list(risk.get("components")),
        "nets": _normalize_string_list(risk.get("nets")),
        "raw": risk,
    }


def _normalize_risk_list(risks: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for risk in risks or []:
        if isinstance(risk, dict):
            normalized.append(_normalize_risk(risk))
    return normalized


def _build_transparency(risk: Dict[str, Any]) -> Dict[str, Any]:
    message = _normalize_message(risk.get("message"))
    message_lower = message.lower()
    severity = _normalize_severity(risk.get("severity"))
    category = _format_category_name(risk.get("category"))
    recommendation = _normalize_recommendation(risk.get("recommendation"))

    components = _normalize_string_list(risk.get("components"))
    nets = _normalize_string_list(risk.get("nets"))

    if "trace" in message_lower and "width" in message_lower:
        trigger = "Trace width condition triggered the rule."
        threshold = "Minimum acceptable trace width for the relevant electrical or manufacturing context."
        observed_value = "A trace width condition was flagged as being below the expected safe range."
        reasoning = (
            "Narrow traces can increase resistance and heat buildup, especially when current demand rises."
        )
        engineering_impact = (
            "This can reduce reliability, increase thermal stress, and create failure risk under load."
        )
    elif "clearance" in message_lower or "spacing" in message_lower or "too close" in message_lower:
        trigger = "Clearance or spacing condition triggered the rule."
        threshold = "Minimum spacing requirement based on voltage, manufacturability, or layout constraints."
        observed_value = "A spacing condition was flagged as being tighter than the expected safe range."
        reasoning = (
            "Insufficient spacing can increase the chance of shorts, crowd routing, assembly difficulty, or thermal coupling."
        )
        engineering_impact = (
            "This can create electrical reliability problems, layout congestion, or manufacturability issues."
        )
    elif "via" in message_lower:
        trigger = "Via-related geometry or usage condition triggered the rule."
        threshold = "Expected via sizing, current handling, or manufacturability constraint."
        observed_value = "A via condition was detected that appears outside the recommended design range."
        reasoning = (
            "Improper via design can weaken current flow, thermal performance, or mechanical reliability."
        )
        engineering_impact = (
            "This can reduce robustness over time and increase the chance of thermal or interconnect issues."
        )
    elif "impedance" in message_lower:
        trigger = "Impedance-related routing condition triggered the rule."
        threshold = "Expected impedance control requirement for the affected signal path."
        observed_value = "A routing or stackup condition suggests impedance may not remain within target."
        reasoning = (
            "Impedance mismatch can degrade signal integrity and create reflection or timing issues."
        )
        engineering_impact = (
            "This can reduce communication reliability and hurt performance in high-speed interfaces."
        )
    elif "return path" in message_lower:
        trigger = "Return-path continuity condition triggered the rule."
        threshold = "Expected continuous return-path support for the affected signal route."
        observed_value = "A signal path appears to have weaker or disrupted return-path support."
        reasoning = (
            "Broken or weak return paths can increase EMI risk and degrade signal quality."
        )
        engineering_impact = (
            "This can create noise, emissions problems, and unstable electrical behavior."
        )
    elif "thermal" in message_lower or "hotspot" in message_lower:
        trigger = "Thermal proximity or heat concentration condition triggered the rule."
        threshold = "Expected component spacing or heat spreading condition for thermal safety."
        observed_value = "A local thermal condition was flagged as likely to concentrate heat."
        reasoning = (
            "Component proximity and weak heat spreading can increase local temperature concentration."
        )
        engineering_impact = (
            "This can reduce reliability, worsen component stress, and create long-term thermal stability issues."
        )
    else:
        trigger = "A rule-based design condition triggered this finding."
        threshold = "A predefined engineering rule or expected design threshold was crossed."
        observed_value = "The current design matched the condition used to raise this finding."
        reasoning = (
            f"This {severity} severity issue in {category} indicates the design may not meet a recommended engineering practice."
        )
        engineering_impact = (
            "Depending on the underlying condition, this may affect reliability, performance, manufacturability, or review confidence."
        )

    evidence_summary_parts: List[str] = []

    if components:
        preview = ", ".join(components[:3])
        if len(components) > 3:
            preview += f" +{len(components) - 3} more"
        evidence_summary_parts.append(f"Components involved: {preview}.")

    if nets:
        preview = ", ".join(nets[:3])
        if len(nets) > 3:
            preview += f" +{len(nets) - 3} more"
        evidence_summary_parts.append(f"Nets involved: {preview}.")

    if recommendation:
        evidence_summary_parts.append(f"Suggested action: {recommendation}")

    evidence_summary = " ".join(evidence_summary_parts).strip()

    return {
        "trigger": trigger,
        "threshold": threshold,
        "observed_value": observed_value,
        "reasoning": reasoning,
        "engineering_impact": engineering_impact,
        "evidence_summary": evidence_summary,
    }


def summarize_score_change(old_score: Optional[float], new_score: Optional[float]) -> Dict[str, Any]:
    old_value = float(old_score or 0)
    new_value = float(new_score or 0)
    delta = round(new_value - old_value, 2)

    if delta > 0:
        direction = "up"
        summary = f"Score improved by {abs(delta):g} points."
        engineering_summary = (
            f"The latest revision improved from {old_value:g} to {new_value:g}, "
            "which suggests a healthier overall risk profile."
        )
    elif delta < 0:
        direction = "down"
        summary = f"Score decreased by {abs(delta):g} points."
        engineering_summary = (
            f"The latest revision dropped from {old_value:g} to {new_value:g}, "
            "which suggests new or more severe findings are affecting design quality."
        )
    else:
        direction = "flat"
        summary = "Score did not change."
        engineering_summary = (
            f"Both revisions scored {new_value:g}, so overall risk level remained stable."
        )

    return {
        "old_score": round(old_value, 2),
        "new_score": round(new_value, 2),
        "delta": delta,
        "direction": direction,
        "summary": summary,
        "engineering_summary": engineering_summary,
    }


def diff_risks(
    old_risks: Optional[List[Dict[str, Any]]],
    new_risks: Optional[List[Dict[str, Any]]],
) -> Dict[str, List[Dict[str, Any]]]:
    old_normalized = _normalize_risk_list(old_risks)
    new_normalized = _normalize_risk_list(new_risks)

    old_map = {_risk_identity(risk): risk for risk in old_normalized}
    new_map = {_risk_identity(risk): risk for risk in new_normalized}

    all_keys = set(old_map.keys()) | set(new_map.keys())

    added: List[Dict[str, Any]] = []
    removed: List[Dict[str, Any]] = []
    changed: List[Dict[str, Any]] = []
    unchanged: List[Dict[str, Any]] = []

    for key in all_keys:
        old_risk = old_map.get(key)
        new_risk = new_map.get(key)

        if old_risk and not new_risk:
            removed.append(old_risk)
            continue

        if new_risk and not old_risk:
            added.append(new_risk)
            continue

        if old_risk and new_risk:
            old_severity = old_risk.get("severity")
            new_severity = new_risk.get("severity")

            if old_severity != new_severity:
                changed.append(
                    {
                        "rule_id": new_risk.get("rule_id") or old_risk.get("rule_id"),
                        "category": new_risk.get("category") or old_risk.get("category"),
                        "message": new_risk.get("message") or old_risk.get("message"),
                        "recommendation": new_risk.get("recommendation") or old_risk.get("recommendation"),
                        "old_severity": old_severity,
                        "new_severity": new_severity,
                        "delta_weight": _severity_weight(new_severity) - _severity_weight(old_severity),
                        "components": new_risk.get("components") or old_risk.get("components") or [],
                        "nets": new_risk.get("nets") or old_risk.get("nets") or [],
                        "old_risk": old_risk,
                        "new_risk": new_risk,
                    }
                )
            else:
                unchanged.append(new_risk)

    added.sort(key=lambda item: (_severity_weight(item.get("severity")) * -1, item.get("category", "")))
    removed.sort(key=lambda item: (_severity_weight(item.get("severity")) * -1, item.get("category", "")))
    changed.sort(key=lambda item: (abs(item.get("delta_weight", 0)) * -1, item.get("category", "")))
    unchanged.sort(key=lambda item: (_severity_weight(item.get("severity")) * -1, item.get("category", "")))

    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged": unchanged,
    }


def calculate_category_impacts(
    added_risks: Optional[List[Dict[str, Any]]] = None,
    removed_risks: Optional[List[Dict[str, Any]]] = None,
    changed_risks: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    category_totals: Dict[str, int] = defaultdict(int)
    details: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {
            "added_count": 0,
            "removed_count": 0,
            "severity_increase_count": 0,
            "severity_decrease_count": 0,
        }
    )

    for risk in added_risks or []:
        category = _normalize_category(risk.get("category"))
        weight = _severity_weight(risk.get("severity"))
        category_totals[category] += weight
        details[category]["added_count"] += 1

    for risk in removed_risks or []:
        category = _normalize_category(risk.get("category"))
        weight = _severity_weight(risk.get("severity"))
        category_totals[category] -= weight
        details[category]["removed_count"] += 1

    for risk in changed_risks or []:
        category = _normalize_category(risk.get("category"))
        delta_weight = int(risk.get("delta_weight", 0))
        category_totals[category] += delta_weight

        if delta_weight > 0:
            details[category]["severity_increase_count"] += 1
        elif delta_weight < 0:
            details[category]["severity_decrease_count"] += 1

    impacts: List[Dict[str, Any]] = []

    for category, delta in category_totals.items():
        if delta > 0:
            direction = "worse"
        elif delta < 0:
            direction = "better"
        else:
            direction = "flat"

        impacts.append(
            {
                "category": _format_category_name(category),
                "raw_category": category,
                "delta": delta,
                "abs_delta": abs(delta),
                "direction": direction,
                "summary": _build_category_summary(category, delta, details.get(category, {})),
                "details": details.get(category, {}),
            }
        )

    impacts.sort(key=lambda item: (-item["abs_delta"], item["category"].lower()))
    return impacts


def _build_category_summary(category: str, delta: int, detail_counts: Dict[str, int]) -> str:
    category_name = _format_category_name(category)

    if delta > 0:
        base = f"{category_name} drove negative movement in this comparison."
    elif delta < 0:
        base = f"{category_name} showed measurable improvement in this comparison."
    else:
        base = f"{category_name} remained broadly stable in this comparison."

    parts: List[str] = []

    added_count = detail_counts.get("added_count", 0)
    removed_count = detail_counts.get("removed_count", 0)
    severity_increase_count = detail_counts.get("severity_increase_count", 0)
    severity_decrease_count = detail_counts.get("severity_decrease_count", 0)

    if added_count:
        parts.append(f"{added_count} new {_pluralize('issue', added_count)}")
    if removed_count:
        parts.append(f"{removed_count} {_pluralize('issue', removed_count)} removed")
    if severity_increase_count:
        parts.append(f"{severity_increase_count} severity {_pluralize('increase', severity_increase_count)}")
    if severity_decrease_count:
        parts.append(f"{severity_decrease_count} severity {_pluralize('decrease', severity_decrease_count)}")

    if not parts:
        return base

    return base + " Main drivers: " + ", ".join(parts) + "."


def _collect_current_high_priority_risks(
    current_risks: Optional[List[Dict[str, Any]]],
    limit: int = 5,
) -> List[Dict[str, Any]]:
    risks = _normalize_risk_list(current_risks)
    risks.sort(key=lambda item: (-_severity_weight(item.get("severity")), item.get("category", "").lower()))
    return risks[:limit]


def _top_current_focus_categories(current_risks: Optional[List[Dict[str, Any]]], limit: int = 3) -> List[str]:
    ordered = []
    for risk in _collect_current_high_priority_risks(current_risks, limit=8):
        category = _format_category_name(risk.get("category"))
        if category not in ordered:
            ordered.append(category)
    return ordered[:limit]


def _build_evidence_points(risk: Dict[str, Any]) -> List[str]:
    evidence: List[str] = []

    rule_id = _safe_str(risk.get("rule_id"), "")
    if rule_id:
        evidence.append(f"Rule ID: {rule_id}")

    severity = _normalize_severity(risk.get("severity"))
    if severity:
        evidence.append(f"Severity: {severity.title()}")

    category = _format_category_name(risk.get("category"))
    if category:
        evidence.append(f"Category: {category}")

    components = _normalize_string_list(risk.get("components"))
    if components:
        preview = ", ".join(components[:3])
        if len(components) > 3:
            preview += f" +{len(components) - 3} more"
        evidence.append(f"Components: {preview}")

    nets = _normalize_string_list(risk.get("nets"))
    if nets:
        preview = ", ".join(nets[:3])
        if len(nets) > 3:
            preview += f" +{len(nets) - 3} more"
        evidence.append(f"Nets: {preview}")

    message = _normalize_message(risk.get("message"))
    if message and message != "Unnamed issue":
        evidence.append(f"Finding: {message}")

    return evidence


def _score_risk_confidence(risk: Dict[str, Any], change_type: str = "current") -> Dict[str, Any]:
    score = 45
    reasons: List[str] = []

    rule_id = _safe_str(risk.get("rule_id"), "")
    if rule_id:
        score += 12
        reasons.append("Rule identifier is present.")

    category = _safe_str(risk.get("category"), "")
    if category:
        score += 8
        reasons.append("Category is defined.")

    message = _normalize_message(risk.get("message"))
    if message and message != "Unnamed issue":
        score += 10
        reasons.append("Finding description is available.")

    recommendation = _safe_str(risk.get("recommendation"), "")
    if recommendation:
        score += 8
        reasons.append("Recommendation is available.")

    components = _normalize_string_list(risk.get("components"))
    if components:
        score += 8
        reasons.append("Specific component evidence is available.")

    nets = _normalize_string_list(risk.get("nets"))
    if nets:
        score += 8
        reasons.append("Specific net evidence is available.")

    severity = _normalize_severity(risk.get("severity"))
    if severity in {"high", "critical"}:
        score += 4
        reasons.append("Higher severity increases review priority and confidence visibility.")

    if change_type == "changed":
        score += 5
        reasons.append("Finding is traceable across revisions.")
    elif change_type in {"added", "removed"}:
        score += 3
        reasons.append("Finding change is directly observable between revisions.")

    score = max(0, min(score, 100))

    if score >= 80:
        band = "high"
    elif score >= 60:
        band = "medium"
    else:
        band = "low"

    if score >= 75:
        signal_level = "signal"
    elif score >= 55:
        signal_level = "review"
    else:
        signal_level = "noise_watch"

    return {
        "score": score,
        "band": band,
        "signal_level": signal_level,
        "reasons": reasons[:4],
        "evidence_points": _build_evidence_points(risk),
    }


def _enrich_risk_list_with_confidence(
    risks: Optional[List[Dict[str, Any]]],
    change_type: str,
) -> List[Dict[str, Any]]:
    enriched: List[Dict[str, Any]] = []

    for risk in risks or []:
        if not isinstance(risk, dict):
            continue

        trust = _score_risk_confidence(risk, change_type=change_type)
        enriched_risk = dict(risk)
        enriched_risk["confidence"] = trust
        enriched_risk["evidence_points"] = trust.get("evidence_points", [])
        enriched_risk["transparency"] = _build_transparency(risk)
        enriched.append(enriched_risk)

    return enriched


def _enrich_changed_risks_with_confidence(changed_risks: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    enriched: List[Dict[str, Any]] = []

    for risk in changed_risks or []:
        if not isinstance(risk, dict):
            continue

        proxy = {
            "rule_id": risk.get("rule_id"),
            "category": risk.get("category"),
            "severity": risk.get("new_severity"),
            "message": risk.get("message"),
            "recommendation": risk.get("recommendation"),
            "components": risk.get("components") or [],
            "nets": risk.get("nets") or [],
        }

        trust = _score_risk_confidence(proxy, change_type="changed")
        enriched_risk = dict(risk)
        enriched_risk["confidence"] = trust
        enriched_risk["evidence_points"] = trust.get("evidence_points", [])
        enriched_risk["transparency"] = _build_transparency(proxy)
        enriched.append(enriched_risk)

    return enriched


def _extract_cluster_key_from_message(message: str) -> str:
    text = _normalize_message(message).lower()

    replacements = [
        (" are too close ", " too close "),
        (" is too close ", " too close "),
        (" may create a thermal hotspot ", " thermal hotspot "),
        (" creates a thermal hotspot ", " thermal hotspot "),
        (" may be too close ", " too close "),
        ("  ", " "),
    ]

    for old, new in replacements:
        text = text.replace(old, new)

    if "(" in text:
        text = text.split("(", 1)[0].strip()

    for prefix in ["finding:", "issue:"]:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()

    return text


def _build_cluster_signature(risk: Dict[str, Any], change_type: str) -> Tuple[str, str, str]:
    category = _normalize_category(risk.get("category"))
    severity = _normalize_severity(risk.get("severity") or risk.get("new_severity"))
    message_key = _extract_cluster_key_from_message(risk.get("message", ""))
    return (
        change_type.lower(),
        category.lower(),
        message_key,
    )


def _cluster_single_risk_group(risks: List[Dict[str, Any]], change_type: str) -> Dict[str, Any]:
    representative = risks[0]
    category = _format_category_name(representative.get("category"))
    severity = _normalize_severity(representative.get("severity") or representative.get("new_severity"))
    base_message = representative.get("message", "Unnamed issue")
    cluster_key = _extract_cluster_key_from_message(base_message)

    recommendations = []
    seen_recommendations = set()
    evidence_points = []
    seen_evidence = set()

    confidence_scores = []
    change_type_counts: Dict[str, int] = defaultdict(int)

    for item in risks:
        conf = item.get("confidence", {})
        confidence_scores.append(int(conf.get("score", 0)))
        local_change_type = _safe_str(item.get("change_type", change_type), change_type)
        change_type_counts[local_change_type] += 1

        recommendation = _safe_str(item.get("recommendation"), "")
        if recommendation and recommendation.lower() not in seen_recommendations:
            seen_recommendations.add(recommendation.lower())
            recommendations.append(recommendation)

        for point in item.get("evidence_points", [])[:3]:
            key = point.lower()
            if key in seen_evidence:
                continue
            seen_evidence.add(key)
            evidence_points.append(point)

    average_confidence = round(sum(confidence_scores) / len(confidence_scores), 1) if confidence_scores else 0
    max_confidence = max(confidence_scores) if confidence_scores else 0

    if len(risks) == 1:
        summary = base_message
    else:
        summary = f"{len(risks)} similar {category.lower()} findings grouped under “{cluster_key}”."

    if max_confidence >= 80:
        confidence_band = "high"
    elif max_confidence >= 60:
        confidence_band = "medium"
    else:
        confidence_band = "low"

    return {
        "cluster_key": cluster_key,
        "change_type": change_type,
        "category": category,
        "severity": severity,
        "message": base_message,
        "summary": summary,
        "count": len(risks),
        "average_confidence": average_confidence,
        "max_confidence": max_confidence,
        "confidence_band": confidence_band,
        "recommendations": recommendations[:3],
        "evidence_points": evidence_points[:5],
        "items": risks,
    }


def _cluster_risk_list(risks: Optional[List[Dict[str, Any]]], change_type: str) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = defaultdict(list)

    for risk in risks or []:
        if not isinstance(risk, dict):
            continue
        grouped[_build_cluster_signature(risk, change_type)].append(risk)

    clusters: List[Dict[str, Any]] = []
    for _, items in grouped.items():
        items.sort(
            key=lambda item: (
                -int(item.get("confidence", {}).get("score", 0)),
                -_severity_weight(item.get("severity") or item.get("new_severity")),
                _normalize_message(item.get("message")),
            )
        )
        clusters.append(_cluster_single_risk_group(items, change_type))

    clusters.sort(
        key=lambda cluster: (
            -cluster.get("count", 0),
            -cluster.get("max_confidence", 0),
            -_severity_weight(cluster.get("severity")),
            cluster.get("category", "").lower(),
            cluster.get("cluster_key", "").lower(),
        )
    )

    return clusters


def _build_noise_reduction_summary(
    added_risks: List[Dict[str, Any]],
    removed_risks: List[Dict[str, Any]],
    changed_risks: List[Dict[str, Any]],
    clustered_added: List[Dict[str, Any]],
    clustered_removed: List[Dict[str, Any]],
    clustered_changed: List[Dict[str, Any]],
) -> Dict[str, Any]:
    raw_total = len(added_risks) + len(removed_risks) + len(changed_risks)
    clustered_total = len(clustered_added) + len(clustered_removed) + len(clustered_changed)
    suppressed_count = max(0, raw_total - clustered_total)

    if raw_total <= 0:
        reduction_pct = 0
    else:
        reduction_pct = round((suppressed_count / raw_total) * 100, 1)

    if suppressed_count == 0:
        summary = "No meaningful duplicate-like findings were grouped in this comparison."
    else:
        summary = (
            f"Grouped {suppressed_count} repeated or highly similar findings into {clustered_total} clearer review groups "
            f"for a {reduction_pct}% reduction in visible comparison noise."
        )

    return {
        "raw_total": raw_total,
        "clustered_total": clustered_total,
        "suppressed_count": suppressed_count,
        "reduction_pct": reduction_pct,
        "summary": summary,
    }


def _build_confidence_summary(
    added_risks: List[Dict[str, Any]],
    removed_risks: List[Dict[str, Any]],
    changed_risks: List[Dict[str, Any]],
) -> Dict[str, Any]:
    all_items = added_risks + removed_risks + changed_risks
    scores = [item.get("confidence", {}).get("score", 0) for item in all_items]

    if not scores:
        return {
            "average_score": 0,
            "band": "low",
            "summary": "No finding-level confidence data was generated for this comparison.",
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
        }

    average_score = round(sum(scores) / len(scores), 1)
    high_count = sum(1 for score in scores if score >= 80)
    medium_count = sum(1 for score in scores if 60 <= score < 80)
    low_count = sum(1 for score in scores if score < 60)

    if average_score >= 80:
        band = "high"
        summary = "Most comparison findings have strong supporting detail and are high-confidence."
    elif average_score >= 60:
        band = "medium"
        summary = "Comparison findings have moderate support overall, with some items needing closer review."
    else:
        band = "low"
        summary = "Several comparison findings have limited supporting detail and should be reviewed carefully."

    return {
        "average_score": average_score,
        "band": band,
        "summary": summary,
        "high_count": high_count,
        "medium_count": medium_count,
        "low_count": low_count,
    }


def _build_signal_summary(
    added_risks: List[Dict[str, Any]],
    removed_risks: List[Dict[str, Any]],
    changed_risks: List[Dict[str, Any]],
) -> Dict[str, Any]:
    all_items = added_risks + removed_risks + changed_risks

    signal_count = sum(
        1 for item in all_items
        if item.get("confidence", {}).get("signal_level") == "signal"
    )
    review_count = sum(
        1 for item in all_items
        if item.get("confidence", {}).get("signal_level") == "review"
    )
    noise_watch_count = sum(
        1 for item in all_items
        if item.get("confidence", {}).get("signal_level") == "noise_watch"
    )

    if signal_count > max(review_count, noise_watch_count):
        summary = "Most meaningful comparison movement appears to be strong signal."
    elif noise_watch_count > signal_count:
        summary = "Several findings have lighter supporting detail and should be treated as watch items."
    else:
        summary = "The comparison contains a mix of strong signals and findings that still need review."

    return {
        "signal_count": signal_count,
        "review_count": review_count,
        "noise_watch_count": noise_watch_count,
        "summary": summary,
    }


def _build_trusted_focus_items(
    added_risks: List[Dict[str, Any]],
    removed_risks: List[Dict[str, Any]],
    changed_risks: List[Dict[str, Any]],
    limit: int = 5,
) -> List[Dict[str, Any]]:
    clustered_added = _cluster_risk_list(added_risks, "added")
    clustered_changed = _cluster_risk_list(changed_risks, "changed")
    clustered_removed = _cluster_risk_list(removed_risks, "removed")

    focus_items: List[Dict[str, Any]] = []

    for cluster in clustered_added:
        representative = cluster.get("items", [{}])[0]
        focus_items.append(
            {
                "change_type": "added",
                "category": cluster.get("category", _format_category_name(representative.get("category"))),
                "message": representative.get("message", "Unnamed issue"),
                "summary": cluster.get("summary", ""),
                "cluster_count": cluster.get("count", 1),
                "severity": _normalize_severity(representative.get("severity")),
                "confidence": representative.get("confidence", {}),
                "evidence_points": representative.get("evidence_points", []),
                "transparency": representative.get("transparency", {}),
                "recommendation": representative.get("recommendation", ""),
            }
        )

    for cluster in clustered_changed:
        representative = cluster.get("items", [{}])[0]
        focus_items.append(
            {
                "change_type": "changed",
                "category": cluster.get("category", _format_category_name(representative.get("category"))),
                "message": representative.get("message", "Unnamed issue"),
                "summary": cluster.get("summary", ""),
                "cluster_count": cluster.get("count", 1),
                "severity": _normalize_severity(representative.get("new_severity")),
                "confidence": representative.get("confidence", {}),
                "evidence_points": representative.get("evidence_points", []),
                "transparency": representative.get("transparency", {}),
                "recommendation": representative.get("recommendation", ""),
                "old_severity": representative.get("old_severity"),
                "new_severity": representative.get("new_severity"),
            }
        )

    for cluster in clustered_removed:
        representative = cluster.get("items", [{}])[0]
        focus_items.append(
            {
                "change_type": "removed",
                "category": cluster.get("category", _format_category_name(representative.get("category"))),
                "message": representative.get("message", "Unnamed issue"),
                "summary": cluster.get("summary", ""),
                "cluster_count": cluster.get("count", 1),
                "severity": _normalize_severity(representative.get("severity")),
                "confidence": representative.get("confidence", {}),
                "evidence_points": representative.get("evidence_points", []),
                "transparency": representative.get("transparency", {}),
                "recommendation": representative.get("recommendation", ""),
            }
        )

    change_type_order = {"added": 0, "changed": 1, "removed": 2}
    focus_items.sort(
        key=lambda item: (
            -int(item.get("confidence", {}).get("score", 0)),
            -int(item.get("cluster_count", 1)),
            -_severity_weight(item.get("severity")),
            change_type_order.get(item.get("change_type"), 9),
            item.get("category", "").lower(),
        )
    )

    return focus_items[:limit]


def build_priority_recommendations(
    category_impacts: Optional[List[Dict[str, Any]]] = None,
    current_risks: Optional[List[Dict[str, Any]]] = None,
    added_risks: Optional[List[Dict[str, Any]]] = None,
    changed_risks: Optional[List[Dict[str, Any]]] = None,
    limit: int = 3,
) -> List[Dict[str, Any]]:
    recommendations: List[Dict[str, Any]] = []

    impacts = category_impacts or []
    worsening = [item for item in impacts if item.get("delta", 0) > 0]
    worsening.sort(key=lambda item: (-item.get("abs_delta", 0), item.get("category", "").lower()))

    top_worsening = worsening[:2]
    for item in top_worsening:
        category = item.get("category", DEFAULT_CATEGORY)
        recommendations.append(
            {
                "title": f"Prioritize {category} review",
                "reason": f"{category} contributed the largest negative movement in this revision comparison.",
                "priority": "high",
                "category": category,
                "type": "category_focus",
            }
        )

    newly_added_high = [
        risk for risk in (added_risks or [])
        if _severity_weight(risk.get("severity")) >= _severity_weight("high")
    ]
    newly_added_high.sort(
        key=lambda item: (
            -int(item.get("confidence", {}).get("score", 0)),
            -_severity_weight(item.get("severity")),
            item.get("category", "").lower(),
        )
    )

    if newly_added_high:
        top_risk = newly_added_high[0]
        category_name = _format_category_name(top_risk.get("category"))
        confidence_band = top_risk.get("confidence", {}).get("band", "medium")
        recommendations.append(
            {
                "title": "Inspect newly introduced severe issue",
                "reason": (
                    f"A new {top_risk.get('severity')} severity finding appeared in {category_name}. "
                    f"This currently looks {confidence_band}-confidence based on available supporting detail."
                ),
                "priority": "high",
                "category": category_name,
                "type": "new_high_severity",
            }
        )

    severity_increases = [risk for risk in (changed_risks or []) if int(risk.get("delta_weight", 0)) > 0]
    severity_increases.sort(
        key=lambda item: (
            -int(item.get("confidence", {}).get("score", 0)),
            -abs(int(item.get("delta_weight", 0))),
            item.get("category", "").lower(),
        )
    )

    if severity_increases:
        top_change = severity_increases[0]
        category_name = _format_category_name(top_change.get("category"))
        recommendations.append(
            {
                "title": "Review worsening existing issue",
                "reason": (
                    f"An existing finding in {category_name} increased from "
                    f"{top_change.get('old_severity', 'low')} to {top_change.get('new_severity', 'low')} severity."
                ),
                "priority": "medium",
                "category": category_name,
                "type": "severity_increase",
            }
        )

    categories = _top_current_focus_categories(current_risks, limit=3)
    if categories:
        recommendations.append(
            {
                "title": "Focus on current highest-risk areas",
                "reason": (
                    "The latest revision still has concentrated higher-severity findings in "
                    + ", ".join(categories)
                    + "."
                ),
                "priority": "medium",
                "category": categories[0],
                "type": "current_state_focus",
            }
        )

    if not recommendations:
        recommendations.append(
            {
                "title": "No urgent comparison actions identified",
                "reason": (
                    "This comparison did not introduce obvious negative movement. "
                    "Use detailed finding review to confirm the design remains stable."
                ),
                "priority": "low",
                "category": "General",
                "type": "stability_followup",
            }
        )

    deduped: List[Dict[str, Any]] = []
    seen = set()

    for recommendation in recommendations:
        key = (
            recommendation.get("title", "").lower(),
            recommendation.get("category", "").lower(),
            recommendation.get("type", "").lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(recommendation)

    priority_order = {"high": 0, "medium": 1, "low": 2}
    deduped.sort(key=lambda item: (priority_order.get(item.get("priority", "low"), 2), item.get("title", "").lower()))

    return deduped[:limit]


def _build_overview_summary(
    score_change: Dict[str, Any],
    added_risks: List[Dict[str, Any]],
    removed_risks: List[Dict[str, Any]],
    changed_risks: List[Dict[str, Any]],
    top_worsening_categories: List[Dict[str, Any]],
    top_improving_categories: List[Dict[str, Any]],
) -> str:
    parts: List[str] = [score_change.get("engineering_summary", score_change.get("summary", "Comparison completed."))]

    if added_risks:
        parts.append(f"{len(added_risks)} new {_pluralize('finding', len(added_risks))} were introduced.")
    if removed_risks:
        parts.append(f"{len(removed_risks)} {_pluralize('finding', len(removed_risks))} were resolved.")
    if changed_risks:
        parts.append(f"{len(changed_risks)} existing {_pluralize('finding', len(changed_risks))} changed severity.")

    if top_worsening_categories:
        worst_names = ", ".join(item.get("category", DEFAULT_CATEGORY) for item in top_worsening_categories[:2])
        parts.append(f"Largest negative drivers were {worst_names}.")

    if top_improving_categories:
        best_names = ", ".join(item.get("category", DEFAULT_CATEGORY) for item in top_improving_categories[:2])
        parts.append(f"Main improvement areas were {best_names}.")

    if not added_risks and not removed_risks and not changed_risks:
        parts.append("No major finding-level movement was detected between these revisions.")

    return " ".join(parts)


def _build_engineering_takeaway(
    score_change: Dict[str, Any],
    top_worsening_categories: List[Dict[str, Any]],
    top_improving_categories: List[Dict[str, Any]],
    stats: Dict[str, int],
) -> str:
    added_count = stats.get("added_count", 0)
    removed_count = stats.get("removed_count", 0)
    changed_count = stats.get("changed_count", 0)

    if score_change.get("direction") == "down":
        if top_worsening_categories:
            names = ", ".join(item.get("category", DEFAULT_CATEGORY) for item in top_worsening_categories[:2])
            return f"The new revision needs closer review, especially in {names}."
        return "The new revision introduced enough negative movement that it should be reviewed before moving forward."

    if score_change.get("direction") == "up":
        if top_improving_categories:
            names = ", ".join(item.get("category", DEFAULT_CATEGORY) for item in top_improving_categories[:2])
            return f"The latest revision is moving in the right direction, with the clearest gains in {names}."
        return "The latest revision improved overall and appears to be reducing risk."

    if added_count == 0 and removed_count == 0 and changed_count == 0:
        return "The two revisions are materially similar from a finding perspective."
    return "The overall score stayed stable, but there are still localized changes worth reviewing."


def _build_trust_summary(
    confidence_summary: Dict[str, Any],
    signal_summary: Dict[str, Any],
    trusted_focus_items: List[Dict[str, Any]],
) -> Dict[str, Any]:
    average_score = confidence_summary.get("average_score", 0)
    high_count = confidence_summary.get("high_count", 0)
    signal_count = signal_summary.get("signal_count", 0)
    watch_count = signal_summary.get("noise_watch_count", 0)

    if average_score >= 80 and signal_count >= watch_count:
        band = "high"
        summary = "Trust signal is strong. Most highlighted comparison findings have good supporting detail."
    elif average_score >= 60:
        band = "medium"
        summary = "Trust signal is moderate. The strongest findings look useful, but some items still need human review."
    else:
        band = "low"
        summary = "Trust signal is limited. Treat this comparison as directional and validate details carefully."

    top_item = trusted_focus_items[0] if trusted_focus_items else None

    return {
        "band": band,
        "summary": summary,
        "top_focus_confidence": top_item.get("confidence", {}).get("score", 0) if top_item else 0,
        "high_confidence_items": high_count,
    }


def generate_comparison_insights(comparison_result: Dict[str, Any]) -> Dict[str, Any]:
    old_score = (
        comparison_result.get("old_score")
        if comparison_result.get("old_score") is not None
        else comparison_result.get("baseline_score")
        if comparison_result.get("baseline_score") is not None
        else comparison_result.get("previous_score")
    )

    new_score = (
        comparison_result.get("new_score")
        if comparison_result.get("new_score") is not None
        else comparison_result.get("current_score")
        if comparison_result.get("current_score") is not None
        else comparison_result.get("latest_score")
    )

    old_risks = (
        comparison_result.get("old_risks")
        if comparison_result.get("old_risks") is not None
        else comparison_result.get("baseline_risks")
        if comparison_result.get("baseline_risks") is not None
        else comparison_result.get("previous_risks")
        if comparison_result.get("previous_risks") is not None
        else []
    )

    new_risks = (
        comparison_result.get("new_risks")
        if comparison_result.get("new_risks") is not None
        else comparison_result.get("current_risks")
        if comparison_result.get("current_risks") is not None
        else comparison_result.get("latest_risks")
        if comparison_result.get("latest_risks") is not None
        else []
    )

    score_change = summarize_score_change(old_score, new_score)
    risk_diff = diff_risks(old_risks, new_risks)

    enriched_added = _enrich_risk_list_with_confidence(risk_diff.get("added", []), change_type="added")
    enriched_removed = _enrich_risk_list_with_confidence(risk_diff.get("removed", []), change_type="removed")
    enriched_changed = _enrich_changed_risks_with_confidence(risk_diff.get("changed", []))

    risk_diff = {
        "added": enriched_added,
        "removed": enriched_removed,
        "changed": enriched_changed,
        "unchanged": risk_diff.get("unchanged", []),
    }

    clustered_added = _cluster_risk_list(risk_diff.get("added", []), "added")
    clustered_removed = _cluster_risk_list(risk_diff.get("removed", []), "removed")
    clustered_changed = _cluster_risk_list(risk_diff.get("changed", []), "changed")

    category_impacts = calculate_category_impacts(
        added_risks=risk_diff.get("added", []),
        removed_risks=risk_diff.get("removed", []),
        changed_risks=risk_diff.get("changed", []),
    )

    top_worsening_categories = [item for item in category_impacts if item.get("delta", 0) > 0][:3]
    top_improving_categories = [item for item in category_impacts if item.get("delta", 0) < 0][:3]

    recommendations = build_priority_recommendations(
        category_impacts=category_impacts,
        current_risks=new_risks,
        added_risks=risk_diff.get("added", []),
        changed_risks=risk_diff.get("changed", []),
        limit=3,
    )

    stats = {
        "added_count": len(risk_diff.get("added", [])),
        "removed_count": len(risk_diff.get("removed", [])),
        "changed_count": len(risk_diff.get("changed", [])),
        "unchanged_count": len(risk_diff.get("unchanged", [])),
        "old_risk_count": len(_normalize_risk_list(old_risks)),
        "new_risk_count": len(_normalize_risk_list(new_risks)),
    }

    overview_summary = _build_overview_summary(
        score_change=score_change,
        added_risks=risk_diff.get("added", []),
        removed_risks=risk_diff.get("removed", []),
        changed_risks=risk_diff.get("changed", []),
        top_worsening_categories=top_worsening_categories,
        top_improving_categories=top_improving_categories,
    )

    engineering_takeaway = _build_engineering_takeaway(
        score_change=score_change,
        top_worsening_categories=top_worsening_categories,
        top_improving_categories=top_improving_categories,
        stats=stats,
    )

    confidence_summary = _build_confidence_summary(
        added_risks=risk_diff.get("added", []),
        removed_risks=risk_diff.get("removed", []),
        changed_risks=risk_diff.get("changed", []),
    )

    signal_summary = _build_signal_summary(
        added_risks=risk_diff.get("added", []),
        removed_risks=risk_diff.get("removed", []),
        changed_risks=risk_diff.get("changed", []),
    )

    trusted_focus_items = _build_trusted_focus_items(
        added_risks=risk_diff.get("added", []),
        removed_risks=risk_diff.get("removed", []),
        changed_risks=risk_diff.get("changed", []),
        limit=5,
    )

    trust_summary = _build_trust_summary(
        confidence_summary=confidence_summary,
        signal_summary=signal_summary,
        trusted_focus_items=trusted_focus_items,
    )

    noise_reduction_summary = _build_noise_reduction_summary(
        added_risks=risk_diff.get("added", []),
        removed_risks=risk_diff.get("removed", []),
        changed_risks=risk_diff.get("changed", []),
        clustered_added=clustered_added,
        clustered_removed=clustered_removed,
        clustered_changed=clustered_changed,
    )

    stability_state = (
        "stable"
        if stats["added_count"] == 0 and stats["removed_count"] == 0 and stats["changed_count"] == 0
        else "changed"
    )

    return {
        "score_change": score_change,
        "overview_summary": overview_summary,
        "engineering_takeaway": engineering_takeaway,
        "stability_state": stability_state,
        "risk_diff": risk_diff,
        "category_impacts": category_impacts,
        "top_worsening_categories": top_worsening_categories,
        "top_improving_categories": top_improving_categories,
        "recommendations": recommendations,
        "stats": stats,
        "confidence_summary": confidence_summary,
        "signal_summary": signal_summary,
        "trust_summary": trust_summary,
        "trusted_focus_items": trusted_focus_items,
        "clustered_added_risks": clustered_added,
        "clustered_removed_risks": clustered_removed,
        "clustered_changed_risks": clustered_changed,
        "noise_reduction_summary": noise_reduction_summary,
    }