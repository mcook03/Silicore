from collections import defaultdict


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _format_name(value, fallback="General"):
    text = str(value or "").strip().replace("_", " ")
    return text.title() if text else fallback


def _severity_weight(value):
    return {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(str(value or "").lower(), 1)


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _compact(text, limit=116):
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def _confidence_band(value):
    if value >= 80:
        return "High"
    if value >= 60:
        return "Moderate"
    return "Low"


def _score_posture(score):
    if score >= 82:
        return "Strong"
    if score >= 68:
        return "Viable"
    if score >= 50:
        return "Watch"
    return "At Risk"


def _top_domains(risks, limit=3):
    counts = defaultdict(int)
    for risk in risks or []:
        counts[_format_name(risk.get("design_domain") or risk.get("category"))] += 1
    items = [{"label": label, "value": count} for label, count in counts.items() if count > 0]
    items.sort(key=lambda item: (-item["value"], item["label"].lower()))
    return items[:limit]


def _dominant_domain(risks):
    items = _top_domains(risks, limit=1)
    return items[0]["label"] if items else "General"


def _dominant_failure_mode(risks):
    dominant = _dominant_domain(risks).lower()
    mapping = {
        "signal integrity": "Signal timing or integrity failure during high-speed operation",
        "power integrity": "Power instability or voltage droop under load",
        "Power Path": "Power-path loss, bottleneck heating, or parasitic instability",
        "Emi Emc": "EMI or return-path behavior causing real-world instability",
        "Stackup Return Path": "Return-current discontinuity and stackup containment issues",
        "Manufacturability": "Fabrication or assembly escapes affecting build quality",
        "Thermal": "Localized thermal hotspot or heat spreading weakness",
        "Safety High Voltage": "Clearance or isolation failure in high-voltage regions",
        "Reliability": "Grounding or robustness failure outside lab conditions",
    }
    for key, value in mapping.items():
        if dominant == key.lower():
            return value
    return "Multi-domain engineering risk that still needs structured review"


def _evidence_depth(risk):
    count = 0
    if risk.get("components"):
        count += len(risk.get("components") or [])
    if risk.get("nets"):
        count += len(risk.get("nets") or [])
    if risk.get("metrics"):
        count += len(risk.get("metrics") or {})
    if risk.get("trigger_condition"):
        count += 1
    if risk.get("threshold_label"):
        count += 1
    if risk.get("observed_label"):
        count += 1
    if risk.get("design_domain"):
        count += 1
    return count


def _fix_priority_label(item):
    raw = item.get("fix_priority") or item.get("priority") or "Medium"
    return _format_name(raw, "Medium")


def _build_validation_step(item):
    category = item.get("category") or "this domain"
    label = item.get("label") or item.get("title") or "the main issue"
    confidence = item.get("confidence_score")
    confidence_note = (
        f" Confidence is {confidence}."
        if confidence not in [None, ""]
        else ""
    )
    return f"After fixing {label.lower()}, rerun {category.lower()} review and confirm the priority driver drops materially.{confidence_note}"


def _build_prompt_starters(items, domain):
    prompts = [
        "What should I fix first on this board?",
        f"Why is {domain.lower()} driving this review?",
        "What should I validate after the next revision?",
    ]
    if items:
        first = items[0].get("title") or items[0].get("label")
        if first:
            prompts[0] = f"Why is '{first}' ranked first?"
    return prompts


def _project_systemic_pattern(workspace_intelligence):
    focus_items = workspace_intelligence.get("trusted_focus_items", []) or []
    if focus_items:
        return focus_items[0].get("category") or "Repeated engineering risk"
    actions = workspace_intelligence.get("next_actions", []) or []
    if actions:
        return actions[0].get("category") or "Repeated engineering risk"
    return "No systemic pattern yet"


def _compare_direction(score_diff, risk_diff, critical_diff):
    if score_diff > 0 and risk_diff <= 0 and critical_diff <= 0:
        return "improving"
    if score_diff < 0 or risk_diff > 0 or critical_diff > 0:
        return "regressing"
    return "mixed"


def _conversation_route(key, label, title, answer, detail="", follow_ups=None, keywords=None):
    return {
        "key": key,
        "label": label,
        "title": title,
        "answer": answer,
        "detail": detail,
        "follow_ups": follow_ups or [],
        "keywords": keywords or [],
    }


def build_board_copilot_brief(result, decision_data):
    result = result or {}
    decision_data = decision_data or {}
    risks = result.get("risks", []) or []
    next_actions = decision_data.get("next_actions", []) or []
    domain = _dominant_domain(risks)
    critical_count = sum(1 for risk in risks if str(risk.get("severity", "")).lower() == "critical")
    score = _safe_float(result.get("display_score", result.get("score")), 0.0)
    average_confidence = _safe_float(decision_data.get("average_confidence"), 0.0)
    top_domains = _top_domains(risks)
    pressure_mix = []
    for item in top_domains[:3]:
        pressure_mix.append(f"{item['label']} ({item['value']})")

    if critical_count > 0 or score < 45:
        posture = "This board is not ready for release confidence yet."
    elif score < 70:
        posture = "This board is directionally viable, but it still needs targeted cleanup before trust is strong."
    else:
        posture = "This board is trending healthy, with a smaller set of issues worth clearing before signoff."

    mission = (
        f"Focus first on {domain} because it is driving the highest concentration of engineering pressure on this board."
        if risks else "Run an analysis to activate Atlas Intelligence for this board."
    )

    fixes = []
    for item in next_actions[:3]:
        fixes.append(
            {
                "title": item.get("label") or item.get("category") or "Review finding",
                "category": item.get("category") or domain,
                "why": item.get("message_short") or item.get("message") or "No finding detail preserved.",
                "action": item.get("recommendation_short") or item.get("recommendation") or "Review this issue in layout.",
                "confidence_score": item.get("confidence_score"),
                "priority_score": item.get("priority_score"),
                "fix_priority": _fix_priority_label(item),
                "validation": _build_validation_step(item),
                "components": item.get("components") or [],
                "nets": item.get("nets") or [],
                "rule_id": item.get("rule_id") or "unknown_rule",
                "trigger_condition": item.get("trigger_condition") or "No trigger condition preserved.",
                "threshold_label": item.get("threshold_label") or "No threshold preserved.",
                "observed_label": item.get("observed_label") or "No observed value preserved.",
                "reasoning": item.get("reasoning") or item.get("message") or "No reasoning preserved.",
                "engineering_impact": item.get("engineering_impact") or "Engineering impact was not explicitly preserved.",
            }
        )

    if fixes:
        validation_plan = [item["validation"] for item in fixes[:2]]
        validation_plan.append("Check whether the board score rises with fewer critical and high-severity findings, not just fewer total flags.")
        validation_plan.append("Confirm confidence and traceability stay stable so the next review is still defensible.")
    else:
        validation_plan = [
            "Run a board analysis to activate fix sequencing and validation guidance.",
        ]

    likely_failure_path = (
        f"The board is most exposed to { _dominant_failure_mode(risks).lower() } because {domain.lower()} is the densest pressure area right now."
        if risks else "No failure-path hypothesis is available until a board is analyzed."
    )

    traceability_ready = sum(1 for risk in risks if _evidence_depth(risk) >= 4)
    traceability_ratio = f"{traceability_ready}/{len(risks)}" if risks else "0/0"
    score_posture = _score_posture(score)
    confidence_band = _confidence_band(average_confidence)

    if score >= 80 and average_confidence >= 75 and critical_count == 0:
        release_note = "This board is approaching signoff posture if the top ranked actions validate cleanly."
    elif critical_count > 0:
        release_note = "Do not treat this board as signoff-ready until the critical findings are closed and rechecked."
    else:
        release_note = "This board still needs one more focused fix-and-rerun loop before it feels release-ready."

    return {
        "posture": posture,
        "mission": mission,
        "dominant_domain": domain,
        "failure_mode": _dominant_failure_mode(risks),
        "likely_failure_path": likely_failure_path,
        "fix_plan": fixes,
        "validation_plan": validation_plan,
        "prompt_starters": _build_prompt_starters(fixes, domain),
        "score": round(score, 1),
        "score_posture": score_posture,
        "average_confidence": round(average_confidence, 1),
        "confidence_band": confidence_band,
        "critical_count": critical_count,
        "traceability_ratio": traceability_ratio,
        "traceability_ready": traceability_ready,
        "pressure_mix": pressure_mix,
        "release_note": release_note,
    }


def build_project_copilot_brief(project, workspace_intelligence, timeline_data, project_value_metrics=None):
    project = project or {}
    workspace_intelligence = workspace_intelligence or {}
    timeline_data = timeline_data or {}
    project_value_metrics = project_value_metrics or []
    next_actions = workspace_intelligence.get("next_actions", []) or []
    trend_summary = workspace_intelligence.get("trend_summary") or timeline_data.get("summary") or "No project trend summary yet."
    score_delta = _safe_float(workspace_intelligence.get("score_delta"), 0.0)
    confidence_delta = _safe_float(workspace_intelligence.get("confidence_delta"), 0.0)
    health_score = _safe_float(workspace_intelligence.get("health_score"), 0.0)
    average_confidence = _safe_float(workspace_intelligence.get("average_confidence"), 0.0)
    systemic = _project_systemic_pattern(workspace_intelligence)

    execution_plan = []
    for item in next_actions[:3]:
        execution_plan.append(
            {
                "title": item.get("category") or "Project issue family",
                "why": _compact(item.get("message") or "No recurring pattern detail preserved.", 110),
                "action": _compact(item.get("recommendation") or "Review this project issue family.", 110),
                "priority_score": item.get("priority_score"),
                "confidence_score": item.get("confidence_score"),
            }
        )

    posture = (
        f"Project trend is currently centered around {systemic}, and the workspace should be managed as an iterative review loop rather than isolated runs."
        if project.get("runs")
        else "Link multiple runs into Silicore Nexus to activate Atlas Intelligence at the workspace level."
    )

    if score_delta > 5 and confidence_delta >= 0:
        momentum = "The workspace is gaining credibility over time."
    elif score_delta < -5:
        momentum = "Recent revisions are adding meaningful project-level risk."
    else:
        momentum = "The workspace is moving, but not cleanly enough to call the trajectory settled."

    if health_score >= 80:
        release_readiness = "Workspace health is strong enough to support pre-release review, provided the repeated issue family is still actively watched."
    elif health_score >= 65:
        release_readiness = "The workspace is viable, but repeated issue families still need one more cleanup cycle before signoff feels safe."
    else:
        release_readiness = "This project is still in active engineering cleanup and should not be treated as release-ready."

    metric_notes = []
    if isinstance(project_value_metrics, dict):
        score_delta = project_value_metrics.get("score_delta")
        risk_delta = project_value_metrics.get("risk_delta")
        improvement_label = project_value_metrics.get("improvement_label")
        note = project_value_metrics.get("note")
        if improvement_label:
            metric_notes.append(f"Direction: {improvement_label}.")
        if score_delta is not None:
            metric_notes.append(f"Score delta: {score_delta:+.1f}.")
        if risk_delta is not None:
            metric_notes.append(f"Risk delta: {risk_delta:+d}.")
        if note:
            metric_notes.append(str(note))
    elif isinstance(project_value_metrics, list):
        for item in project_value_metrics[:3]:
            label = item.get("label") or "Value"
            value = item.get("value") or "0"
            subtext = item.get("subtext") or ""
            metric_notes.append(f"{label}: {value}. {subtext}")

    return {
        "posture": posture,
        "trend_summary": trend_summary,
        "systemic_pattern": systemic,
        "execution_plan": execution_plan,
        "momentum": momentum,
        "health_score": round(health_score, 1),
        "average_confidence": round(average_confidence, 1),
        "confidence_band": _confidence_band(average_confidence),
        "release_readiness": release_readiness,
        "metric_notes": metric_notes,
        "team_guidance": [
            "Assign the top recurring issue family to one owner and track the fix through re-analysis.",
            "Use review notes to capture what changed before each linked rerun.",
            "Judge progress by risk delta and score delta together, not score alone.",
        ],
        "prompt_starters": [
            f"What is the recurring root cause behind {systemic.lower()}?",
            "Which project issue family should the team own first?",
            "Is this workspace improving enough for the next review gate?",
        ],
    }


def build_compare_copilot_brief(comparison):
    comparison = comparison or {}
    insights = comparison.get("insights") or {}
    recommendations = insights.get("recommendations", []) or []
    focus_items = comparison.get("compare_focus_items") or []
    score_diff = _safe_float(comparison.get("score_diff"), 0.0)
    risk_diff = _safe_int(comparison.get("risk_diff"), 0)
    critical_diff = _safe_int(comparison.get("critical_diff"), 0)
    direction = _compare_direction(score_diff, risk_diff, critical_diff)

    if direction == "improving":
        posture = "The new revision is directionally healthier than the baseline."
    elif direction == "regressing":
        posture = "The new revision introduced meaningful regression pressure."
    else:
        posture = "The revision is mixed, so domain-level movement matters more than the headline score alone."

    takeaways = []
    for index, item in enumerate(recommendations[:3]):
        focus_item = focus_items[index] if index < len(focus_items) else {}
        takeaways.append(
            {
                "title": item.get("title") or item.get("category") or "Comparison recommendation",
                "why": _compact(item.get("summary") or item.get("description") or "No comparison rationale preserved.", 120),
                "components": focus_item.get("components") or [],
                "nets": focus_item.get("nets") or [],
                "change_type": focus_item.get("change_type") or "change",
            }
        )

    domain_impacts = insights.get("domain_impacts", []) or []
    lead_domain = domain_impacts[0] if domain_impacts else {}
    lead_domain_name = lead_domain.get("domain") or "General"
    lead_domain_delta = _safe_int(lead_domain.get("delta"), 0)
    if lead_domain_delta > 0:
        root_cause = f"The strongest regression pressure is in {lead_domain_name}, so the changed findings likely share a subsystem-level cause there."
    elif lead_domain_delta < 0:
        root_cause = f"{lead_domain_name} improved the most, so that domain is likely carrying the strongest benefit from the revision."
    else:
        root_cause = "No single engineering domain dominated the revision, so inspect clustered findings before drawing a conclusion."

    if direction == "improving" and critical_diff <= 0:
        signoff_note = "This revision is trending toward acceptance, but it should still be checked in the revision inspector before signoff."
    elif direction == "regressing":
        signoff_note = "This revision should not be treated as signoff-ready until the regressed findings are explained and retested."
    else:
        signoff_note = "The revision needs targeted subsystem review before it can be treated as clearly better or worse."

    return {
        "posture": posture,
        "takeaways": takeaways,
        "next_move": "Use the revision inspector to confirm whether the changed findings cluster in one subsystem before accepting the new revision as healthier.",
        "direction": direction,
        "root_cause": root_cause,
        "signoff_note": signoff_note,
        "score_diff": round(score_diff, 1),
        "risk_diff": risk_diff,
        "critical_diff": critical_diff,
        "prompt_starters": [
            "What got worse in this revision?",
            f"Why did {lead_domain_name.lower()} move the most?",
            "What should I verify before approving this change?",
        ],
    }


def build_board_assistant_console(board_copilot, decision_data):
    board_copilot = board_copilot or {}
    decision_data = decision_data or {}
    actions = decision_data.get("next_actions", []) or []
    top_action = actions[0] if actions else {}
    top_domain = board_copilot.get("dominant_domain") or "General"
    top_action_label = top_action.get("label") or top_action.get("category") or "the top issue"
    validation_steps = (board_copilot.get("validation_plan") or [])[:3]

    routes = [
        _conversation_route(
            "fix_priority",
            "What matters first?",
            "Fix Priority",
            board_copilot.get("mission") or "No board mission is available yet.",
            (
                f"The current fix-first path starts with {top_action_label.lower()} because it combines the strongest severity, confidence, and engineering impact signal."
                if top_action
                else "Run an analysis to activate ranked fix sequencing."
            ),
            [
                "Why is this issue ranked first?",
                "Show the evidence behind that priority",
                "What should I validate after I fix it?",
            ],
            ["fix", "first", "priority", "matter", "important", "rank"],
        ),
        _conversation_route(
            "risk_story",
            "Why is this risky?",
            "Failure Path",
            board_copilot.get("likely_failure_path") or board_copilot.get("failure_mode") or "No failure-path hypothesis is available yet.",
            "Atlas is reading this as a real-world failure mechanism, not just a rule hit, so the key question is what will break first under operating stress.",
            [
                "Which subsystem is driving that risk?",
                "What would failure look like in the lab?",
                "Show me the strongest evidence",
            ],
            ["risk", "risky", "failure", "break", "danger", "concern"],
        ),
        _conversation_route(
            "validation",
            "What do I validate next?",
            "Validation Plan",
            " ".join(validation_steps) or "No validation plan is available yet.",
            "Use the next rerun to confirm the top driver collapses, confidence stays stable, and the score improves for the right reason.",
            [
                "What should I re-measure after the rerun?",
                "How do I know the score improved for the right reason?",
                "Am I signoff ready after that?",
            ],
            ["validate", "validation", "recheck", "rerun", "test", "measure"],
        ),
        _conversation_route(
            "score",
            "Why is the score low?",
            "Score Story",
            " ".join(
                [
                    board_copilot.get("posture") or "",
                    board_copilot.get("mission") or "",
                    board_copilot.get("release_note") or "",
                ]
            ).strip() or "No score explanation is available yet.",
            "Atlas weighs board posture, evidence quality, and release readiness together, so the score is a summary of engineering trust rather than a raw issue count.",
            [
                "What is hurting the score most?",
                "What would raise the score fastest?",
                "Show me the top risk driver",
            ],
            ["score", "low", "rating", "posture", "why"],
        ),
        _conversation_route(
            "signoff",
            "Am I signoff ready?",
            "Signoff Readiness",
            board_copilot.get("release_note") or "No signoff note is available for this board yet.",
            "Treat signoff as a confidence decision. Atlas is looking for strong score posture, no unresolved criticals, and a clean validation loop before calling the board ready.",
            [
                "What blocks signoff right now?",
                "What should I close before release?",
                "Show me the critical evidence",
            ],
            ["signoff", "release", "ready", "approve", "ship"],
        ),
    ]

    questions = [
        {
            "label": "What matters first?",
            "answer": board_copilot.get("mission") or "No board mission is available yet.",
            "route_key": "fix_priority",
        },
        {
            "label": "Why is this risky?",
            "answer": board_copilot.get("likely_failure_path") or board_copilot.get("failure_mode") or "No failure-path hypothesis is available yet.",
            "route_key": "risk_story",
        },
        {
            "label": "What do I validate next?",
            "answer": " ".join((board_copilot.get("validation_plan") or [])[:2]) or "No validation plan is available yet.",
            "route_key": "validation",
        },
    ]

    review_lenses = [
        {
            "label": "Top Driver",
            "headline": f"Center the review on {top_domain}.",
            "copy": board_copilot.get("mission") or "No dominant driver is available yet.",
            "nets": top_action.get("nets") or [],
            "components": top_action.get("components") or [],
            "heat_mode": "heatmap",
            "route_key": "fix_priority",
        },
        {
            "label": "Most Actionable",
            "headline": f"Open {top_action.get('label') or 'the top action'} in context.",
            "copy": top_action.get("recommendation_short") or top_action.get("recommendation") or "No direct recommendation is available yet.",
            "nets": top_action.get("nets") or [],
            "components": top_action.get("components") or [],
            "heat_mode": "hybrid",
            "route_key": "risk_story",
        },
        {
            "label": "Geometry Review",
            "headline": "Drop the heat layer and inspect physical routing.",
            "copy": "Use geometry focus when you need to verify real placement, routing continuity, and board structure without the heat overlay dominating the view.",
            "nets": [],
            "components": [],
            "heat_mode": "normal",
            "route_key": "validation",
        },
    ]

    return {
        "title": "Atlas Intelligence Console",
        "eyebrow": "Atlas Intelligence",
        "summary": board_copilot.get("posture") or "Run a board analysis to activate Atlas Intelligence guidance.",
        "questions": questions,
        "review_lenses": review_lenses,
        "routes": routes,
    }


def build_project_assistant_console(project_copilot):
    project_copilot = project_copilot or {}
    execution_plan = project_copilot.get("execution_plan", []) or []
    first_item = execution_plan[0] if execution_plan else {}
    routes = [
        _conversation_route(
            "recurring_pattern",
            "What is repeating?",
            "Recurring Pattern",
            f"The strongest systemic pattern is {project_copilot.get('systemic_pattern', 'not clear yet')}.",
            project_copilot.get("posture") or "No workspace posture is available yet.",
            [
                "Why does that pattern keep showing up?",
                "Which board or run is contributing most?",
                "What should the team do first?",
            ],
            ["repeat", "repeating", "pattern", "systemic", "recurring"],
        ),
        _conversation_route(
            "workspace_momentum",
            "Are we improving?",
            "Workspace Momentum",
            project_copilot.get("momentum") or project_copilot.get("trend_summary") or "No project momentum readout is available yet.",
            "Atlas is reading both trend direction and trust quality, so improvement only counts if the repeated issue family is genuinely collapsing over time.",
            [
                "What changed most across the timeline?",
                "Are we improving enough for the next gate?",
                "What is still holding the workspace back?",
            ],
            ["improv", "trend", "better", "momentum", "gate"],
        ),
        _conversation_route(
            "team_action",
            "What should the team do next?",
            "Next Team Action",
            first_item.get("action") or "No team execution step is available yet.",
            first_item.get("why") or "The strongest next move should be assigned, tracked, and revalidated through the next workspace cycle.",
            [
                "Who should own this next?",
                "What should we validate after the rerun?",
                "What is the release risk if we skip it?",
            ],
            ["team", "next", "action", "owner", "do now"],
        ),
        _conversation_route(
            "release_gate",
            "Are we review-gate ready?",
            "Release Gate",
            project_copilot.get("release_readiness") or "No release-readiness note is available yet.",
            "Atlas treats the workspace as a review gate, so the question is whether project trend, confidence, and repeated issues are all aligned enough for the next decision.",
            [
                "What blocks the next review gate?",
                "Which repeated issue family matters most?",
                "Show me the trend story",
            ],
            ["release", "gate", "ready", "signoff", "approval"],
        ),
    ]

    questions = [
        {
            "label": "What is repeating?",
            "answer": f"The strongest systemic pattern is {project_copilot.get('systemic_pattern', 'not clear yet')}.",
            "route_key": "recurring_pattern",
        },
        {
            "label": "Are we improving?",
            "answer": project_copilot.get("momentum") or project_copilot.get("trend_summary") or "No project momentum readout is available yet.",
            "route_key": "workspace_momentum",
        },
        {
            "label": "What should the team do next?",
            "answer": first_item.get("action") or "No team execution step is available yet.",
            "route_key": "team_action",
        },
    ]

    review_lenses = [
        {
            "label": "Systemic Pattern",
            "headline": f"Review {project_copilot.get('systemic_pattern', 'the dominant pattern')}.",
            "copy": project_copilot.get("posture") or "No workspace posture is available yet.",
            "route_key": "recurring_pattern",
        },
        {
            "label": "Trend Gate",
            "headline": "Read the workspace as a release gate, not a dashboard.",
            "copy": project_copilot.get("release_readiness") or "No release-readiness note is available yet.",
            "route_key": "release_gate",
        },
        {
            "label": "Team Loop",
            "headline": "Treat the next rerun as a managed engineering cycle.",
            "copy": "Use owner assignment, review notes, and a targeted rerun to verify whether the repeated issue family actually collapsed.",
            "route_key": "team_action",
        },
    ]

    return {
        "title": "Atlas Intelligence Console",
        "eyebrow": "Silicore Nexus",
        "summary": project_copilot.get("posture") or "Link runs into Silicore Nexus to activate the Atlas Intelligence console.",
        "questions": questions,
        "review_lenses": review_lenses,
        "routes": routes,
    }


def build_compare_assistant_console(compare_copilot):
    compare_copilot = compare_copilot or {}
    takeaways = compare_copilot.get("takeaways", []) or []
    first_takeaway = takeaways[0] if takeaways else {}
    routes = [
        _conversation_route(
            "top_change",
            "What changed most?",
            "Top Change Cluster",
            compare_copilot.get("root_cause") or "No dominant revision change is available yet.",
            first_takeaway.get("why") or compare_copilot.get("next_move") or "No comparison cluster is available yet.",
            [
                "Show me what got worse",
                "What should I inspect next?",
                "Can I approve this revision?",
            ],
            ["change", "changed", "difference", "cluster", "moved"],
        ),
        _conversation_route(
            "approval",
            "Can I approve this?",
            "Approval Readiness",
            compare_copilot.get("signoff_note") or "No signoff note is available yet.",
            "Atlas is treating this as an approval gate, so the compare view should confirm whether the changed findings cluster into one explainable subsystem before you accept the revision.",
            [
                "What blocks approval right now?",
                "What got worse in the new revision?",
                "Show me the top change cluster",
            ],
            ["approve", "approval", "signoff", "ready", "accept"],
        ),
        _conversation_route(
            "inspect_next",
            "What do I inspect next?",
            "Next Inspection Step",
            first_takeaway.get("why") or compare_copilot.get("next_move") or "No follow-up inspection step is available yet.",
            "Use the inspector to verify whether the biggest movement is isolated or systemic across the revision.",
            [
                "Why did that subsystem move?",
                "Is this revision actually healthier?",
                "Can I approve this revision?",
            ],
            ["inspect", "next", "focus", "look", "verify"],
        ),
        _conversation_route(
            "regression",
            "What got worse?",
            "What Got Worse",
            compare_copilot.get("root_cause") or "No dominant regression note is available yet.",
            "The important question is whether this is one concentrated regression or a broader shift across multiple engineering domains.",
            [
                "Show me the top change cluster",
                "What should I verify before approval?",
                "Is any domain improving enough to offset it?",
            ],
            ["worse", "regress", "regression", "degraded", "bad"],
        ),
    ]

    questions = [
        {
            "label": "What changed most?",
            "answer": compare_copilot.get("root_cause") or "No dominant revision change is available yet.",
            "route_key": "top_change",
        },
        {
            "label": "Can I approve this?",
            "answer": compare_copilot.get("signoff_note") or "No signoff note is available yet.",
            "route_key": "approval",
        },
        {
            "label": "What do I inspect next?",
            "answer": first_takeaway.get("why") or compare_copilot.get("next_move") or "No follow-up inspection step is available yet.",
            "route_key": "inspect_next",
        },
    ]

    review_lenses = [
        {
            "label": "Top Change Cluster",
            "headline": first_takeaway.get("title") or "Open the top revision change",
            "copy": first_takeaway.get("why") or compare_copilot.get("root_cause") or "No comparison cluster is available yet.",
            "nets": first_takeaway.get("nets") or [],
            "components": first_takeaway.get("components") or [],
            "route_key": "top_change",
        },
        {
            "label": "Revision Signoff",
            "headline": "Use the comparison as an approval gate.",
            "copy": compare_copilot.get("signoff_note") or "No signoff note is available yet.",
            "nets": [],
            "components": [],
            "route_key": "approval",
        },
        {
            "label": "Inspector Focus",
            "headline": "Jump both revisions to the same subsystem.",
            "copy": compare_copilot.get("next_move") or "No inspector guidance is available yet.",
            "nets": first_takeaway.get("nets") or [],
            "components": first_takeaway.get("components") or [],
            "route_key": "inspect_next",
        },
    ]

    return {
        "title": "Atlas Intelligence Console",
        "eyebrow": "Atlas Intelligence",
        "summary": compare_copilot.get("posture") or "Run a comparison to activate the Atlas Intelligence console.",
        "questions": questions,
        "review_lenses": review_lenses,
        "routes": routes,
    }
