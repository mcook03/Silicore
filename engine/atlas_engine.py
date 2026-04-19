from collections import defaultdict


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


def _lower(value):
    return str(value or "").strip().lower()


def _titleize(value, fallback="General"):
    text = str(value or "").strip().replace("_", " ")
    return text.title() if text else fallback


def _compact(text, limit=180):
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def _listify(value):
    if isinstance(value, list):
        return value
    return []


def _keywords(*groups):
    result = []
    for group in groups:
        for item in group:
            cleaned = _lower(item)
            if cleaned:
                result.append(cleaned)
    return result


def _severity_rank(severity):
    return {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(_lower(severity), 1)


def _history_last_intent(history):
    for item in reversed(_listify(history)):
        if isinstance(item, dict) and item.get("intent"):
            return item.get("intent")
    return None


def _prompt_is_follow_up(prompt):
    lower = _lower(prompt)
    tokens = [
        "what else",
        "go deeper",
        "tell me more",
        "expand",
        "more detail",
        "deeper",
        "prove it",
        "show evidence",
    ]
    if any(token in lower for token in tokens):
        return True
    generic_follow_ups = {"why", "how", "and then", "what next", "next?", "then what"}
    return lower in generic_follow_ups


def _pick_top_risks(risk_sources, limit=4, matcher=None):
    items = []
    for item in _listify(risk_sources):
        if matcher and not matcher(item):
            continue
        items.append(item)
    items.sort(
        key=lambda item: (
            -_severity_rank(item.get("severity")),
            -_safe_float(item.get("confidence"), _safe_float(item.get("confidence_score"), 0)),
            _lower(item.get("message")),
        )
    )
    return items[:limit]


def _source_to_citation(item):
    if not isinstance(item, dict):
        return {}
    return {
        "label": item.get("message") or item.get("label") or item.get("title") or "Finding",
        "target": item.get("id") or item.get("target"),
        "components": _listify(item.get("components")),
        "nets": _listify(item.get("nets")),
    }


def _domain_matcher(domain):
    needle = _lower(domain)
    if not needle:
        return lambda item: True

    def _match(item):
        haystack = " ".join(
            [
                _lower(item.get("domain")),
                _lower(item.get("category")),
                _lower(item.get("message")),
                _lower(item.get("design_domain")),
            ]
        )
        return needle in haystack

    return _match


def _extract_domain_rows(context):
    rows = []
    for item in _listify(context.get("domain_breakdown")):
        rows.append(
            {
                "label": item.get("label") or item.get("title") or "General",
                "count": _safe_int(item.get("count") or item.get("value"), 0),
                "severity": item.get("severity") or item.get("severity_label") or "medium",
                "confidence": _safe_float(item.get("confidence"), 0.0),
                "traceability": _safe_float(item.get("traceability"), 0.0),
                "headline": item.get("headline") or item.get("summary") or "",
            }
        )
    rows.sort(key=lambda item: (-item["count"], -item["confidence"], item["label"].lower()))
    return rows


def _extract_value_note(context, label_keyword):
    keyword = _lower(label_keyword)
    for item in _listify(context.get("value_metrics")):
        label = _lower(item.get("label"))
        if keyword in label:
            return f"{item.get('label')}: {item.get('value')}."
    return ""


def _make_response(intent, title, answer, detail="", follow_ups=None, citations=None, actions=None, confidence=0.78):
    return {
        "intent": intent,
        "title": title,
        "answer": answer,
        "detail": detail,
        "follow_ups": follow_ups or [],
        "citations": citations or [],
        "actions": actions or {},
        "confidence": round(_safe_float(confidence, 0.78), 2),
    }


def _resolve_board_intent(prompt, context, history):
    lower = _lower(prompt)
    if _prompt_is_follow_up(prompt):
        return _history_last_intent(history) or "overview"

    mapping = [
        ("signoff", _keywords(["signoff", "release", "ship", "ready", "approve"])),
        ("validation", _keywords(["validate", "validation", "rerun", "recheck", "test", "measure"])),
        ("traceability", _keywords(["traceability", "evidence", "proof", "defensible"])),
        ("cam", _keywords(["gerber", "cam", "bundle", "drill file", "outline layer", "copper layer", "fabrication package"])),
        ("parser", _keywords(["parser", "import", "parse confidence", "geometry confidence", "recognition"])),
        ("physics", _keywords(["physics", "impedance", "ir drop", "current density", "voltage drop", "delay", "modeled"])),
        ("stackup", _keywords(["stackup", "reference plane", "layer stack", "return path layer"])),
        ("subsystem", _keywords(["subsystem", "analog section", "power section", "clocking", "partition"])),
        ("confidence", _keywords(["confidence", "trust", "certainty", "reliable"])),
        ("fix_priority", _keywords(["fix first", "priority", "prioritize", "first", "top issue", "top action"])),
        ("score", _keywords(["score", "rating", "posture"])),
        ("power", _keywords(["power", "voltage", "current", "rail", "decoupling", "supply"])),
        ("signal", _keywords(["signal", "return path", "stackup", "differential", "timing", "crosstalk"])),
        ("thermal", _keywords(["thermal", "heat", "hotspot", "temperature"])),
        ("emi", _keywords(["emi", "emc", "noise", "radiated", "loop", "grounding"])),
        ("manufacturing", _keywords(["dfm", "manufacturing", "assembly", "testability", "dft", "fabrication"])),
        ("safety", _keywords(["safety", "high voltage", "clearance", "creepage", "isolation"])),
    ]
    for intent, words in mapping:
        if any(word in lower for word in words):
            return intent
    return "overview"


def answer_board_question(prompt, context, history=None):
    context = context or {}
    history = history or []
    risk_sources = _listify(context.get("risk_sources"))
    top_actions = _listify(context.get("top_actions"))
    validation_plan = _listify(context.get("validation_plan"))
    domain_rows = _extract_domain_rows(context)
    dominant_domain = context.get("dominant_domain") or (domain_rows[0]["label"] if domain_rows else "General")
    intent = _resolve_board_intent(prompt, context, history)

    def _action_payload(item, heat_mode="hybrid"):
        return {
            "heat_mode": heat_mode,
            "components": _listify(item.get("components")),
            "nets": _listify(item.get("nets")),
            "net": (_listify(item.get("nets")) or [""])[0],
        }

    if intent == "fix_priority":
        top_action = top_actions[0] if top_actions else {}
        citations = [_source_to_citation(item) for item in _pick_top_risks(risk_sources, limit=3)]
        return _make_response(
            "fix_priority",
            "Fix Priority",
            top_action.get("message_short")
            or context.get("mission")
            or f"The strongest fix-first driver on this board is {dominant_domain}.",
            detail=(
                f"Atlas is ranking {top_action.get('label', 'the top issue')} first because it combines severity, confidence, repeated pressure in the same domain, and likely real-world impact."
                if top_action
                else f"Atlas wants you to center the next review cycle on {dominant_domain} before spreading effort across smaller issues."
            ),
            follow_ups=[
                "Why is that issue ranked first?",
                "Show me the evidence behind that priority",
                "What should I validate after I fix it?",
            ],
            citations=citations,
            actions=_action_payload(top_action, "heatmap") if top_action else {},
            confidence=0.86,
        )

    if intent == "score":
        citations = [_source_to_citation(item) for item in _pick_top_risks(risk_sources, limit=3)]
        signoff_gate = context.get("signoff_gate") or {}
        gate_note = (
            f" Release posture is currently {str(signoff_gate.get('label') or signoff_gate.get('decision') or 'validation pending').replace('_', ' ')}."
            if signoff_gate else ""
        )
        return _make_response(
            "score",
            "Score Story",
            context.get("posture") or "No board posture is available yet.",
            detail=(
                f"Score {context.get('score', 0)} / 100 reflects the balance of risk severity, evidence depth, and release readiness. Atlas currently sees {dominant_domain} as the strongest score driver."
                + gate_note
            ),
            follow_ups=[
                "What is hurting the score most?",
                "What would raise the score fastest?",
                "Am I signoff ready?",
            ],
            citations=citations,
            confidence=0.82,
        )

    if intent == "signoff":
        criticals = _pick_top_risks(risk_sources, limit=3, matcher=lambda item: _lower(item.get("severity")) == "critical")
        signoff_gate = context.get("signoff_gate") or {}
        blockers = _listify(signoff_gate.get("blockers"))
        next_checks = _listify(signoff_gate.get("next_checks"))
        parser_confidence = context.get("parser_confidence") or {}
        release_score = signoff_gate.get("release_score")
        answer = signoff_gate.get("summary") or context.get("release_note") or "No signoff note is available for this board yet."
        detail_parts = [
            "Atlas treats signoff as a confidence-backed engineering decision.",
        ]
        if release_score is not None:
            detail_parts.append(f"The current release score is {release_score} / 100.")
        if parser_confidence.get("score"):
            detail_parts.append(f"Parser confidence is {parser_confidence.get('score')} / 100.")
        if blockers:
            detail_parts.append(f"Primary blocker: {blockers[0]}")
        elif next_checks:
            detail_parts.append(f"Next validation move: {next_checks[0]}")
        return _make_response(
            "signoff",
            "Signoff Readiness",
            answer,
            detail=" ".join(detail_parts),
            follow_ups=[
                "What blocks signoff right now?",
                "What should I validate next?",
                "How trustworthy is the parser and model coverage?",
            ],
            citations=[_source_to_citation(item) for item in criticals] or [_source_to_citation(item) for item in _pick_top_risks(risk_sources, limit=2)],
            confidence=0.84,
        )

    if intent == "validation":
        answer = " ".join(str(item) for item in validation_plan[:3]) or "No validation plan is available yet."
        top_action = top_actions[0] if top_actions else {}
        return _make_response(
            "validation",
            "Validation Plan",
            answer,
            detail="The next rerun should prove that the main risk driver collapsed for a physical reason, not just that the total issue count moved.",
            follow_ups=[
                "How do I know the score improved for the right reason?",
                "What matters first before the rerun?",
                "Am I signoff ready after that?",
            ],
            citations=[_source_to_citation(item) for item in _pick_top_risks(risk_sources, limit=2)],
            actions=_action_payload(top_action) if top_action else {},
            confidence=0.8,
        )

    if intent == "traceability":
        traceability_note = _extract_value_note(context, "trace")
        confidence_note = _extract_value_note(context, "confidence")
        answer = traceability_note or confidence_note or "Traceability metrics are not populated yet."
        return _make_response(
            "traceability",
            "Evidence and Traceability",
            answer,
            detail="Atlas uses evidence depth, observed thresholds, and preserved engineering context to decide whether a finding is strong enough to drive action or should stay directional.",
            follow_ups=[
                "Which findings are the most defensible?",
                "Which issues still need manual validation?",
                "What matters first?",
            ],
            citations=[_source_to_citation(item) for item in _pick_top_risks(risk_sources, limit=3)],
            confidence=0.76,
        )

    if intent == "parser":
        parser_confidence = context.get("parser_confidence") or {}
        cam_summary = context.get("cam_summary") or {}
        detail = (
            f"Confidence is {parser_confidence.get('score', 0)} / 100 with "
            f"{parser_confidence.get('component_count', 0)} components, "
            f"{parser_confidence.get('trace_count', 0)} traces, and "
            f"{parser_confidence.get('outline_count', 0)} outline feature(s) recognized."
        )
        if cam_summary.get("active"):
            detail += (
                f" CAM bundle readiness is {cam_summary.get('readiness_score', 0)} / 100 with "
                f"{cam_summary.get('layer_file_count', 0)} file(s), "
                f"{cam_summary.get('outline_count', 0)} outline segment(s), and "
                f"{cam_summary.get('drill_count', 0)} drill hit(s)."
            )
        return _make_response(
            "parser",
            "Parser and Geometry Trust",
            parser_confidence.get("summary") or "Parser confidence is not available for this board yet.",
            detail=detail,
            follow_ups=[
                "How does parser confidence affect signoff?",
                "Is this CAM package complete enough for review?",
                "What assumptions were used in the model?",
                "Show me the strongest evidence",
            ],
            citations=[_source_to_citation(item) for item in _pick_top_risks(risk_sources, limit=2)],
            confidence=0.79,
        )

    if intent == "cam":
        cam_summary = context.get("cam_summary") or {}
        if not cam_summary.get("active"):
            return _make_response(
                "cam",
                "CAM Package Review",
                "This run is not a Gerber/CAM bundle review.",
                detail="Atlas only activates CAM bundle reasoning when the input is a Gerber directory, archive, or CAM layer set.",
                follow_ups=[
                    "How trustworthy is the parser and model coverage?",
                    "Am I signoff ready?",
                ],
                confidence=0.77,
            )
        missing_signals = _listify(cam_summary.get("missing_signals"))
        remediation_steps = _listify(cam_summary.get("remediation_steps"))
        strengths = _listify(cam_summary.get("strengths"))
        fabrication_blockers = _listify(cam_summary.get("fabrication_blockers"))
        geometry_warnings = _listify(cam_summary.get("geometry_warnings"))
        parser_warnings = _listify(cam_summary.get("parser_warnings"))
        source_family = str(cam_summary.get("source_family") or "generic_gerber").replace("_", " ")
        answer = cam_summary.get("summary") or "CAM package review data is available for this board."
        detail_parts = [
            (
                f"{cam_summary.get('status_label', 'CAM review ready')} from {source_family} with "
                f"{cam_summary.get('layer_file_count', 0)} file(s), "
                f"{len(cam_summary.get('copper_layers') or [])} copper layer(s), "
                f"{cam_summary.get('outline_count', 0)} outline segment(s), and "
                f"{cam_summary.get('drill_count', 0)} drill hit(s)."
            )
        ]
        if fabrication_blockers:
            detail_parts.append(f"Main fabrication blocker: {fabrication_blockers[0]}.")
        elif missing_signals:
            detail_parts.append(f"Main package gap: {missing_signals[0]}.")
        if parser_warnings:
            detail_parts.append(f"This looks more like parser trust pressure than a pure package miss: {parser_warnings[0]}.")
        elif geometry_warnings:
            detail_parts.append(f"Geometry review is partially limited: {geometry_warnings[0]}.")
        elif strengths:
            detail_parts.append(f"Strongest recognition signal: {strengths[0]}.")
        if remediation_steps:
            detail_parts.append(f"Next CAM fix: {remediation_steps[0]}")
        if fabrication_blockers and remediation_steps:
            answer += f" For fabrication handoff, ask for: {remediation_steps[0]}"
        return _make_response(
            "cam",
            "CAM Package Review",
            answer,
            detail=" ".join(detail_parts),
            follow_ups=[
                "Is this CAM package complete enough for fabrication review?",
                "How much should I trust this Gerber import?",
                "What should I ask the designer or fabricator to re-export?",
                "Is this a parser issue or a package issue?",
                "Show me the strongest evidence",
            ],
            citations=[_source_to_citation(item) for item in _pick_top_risks(risk_sources, limit=2)],
            confidence=0.83,
        )

    if intent in {"physics", "confidence"}:
        physics_summary = context.get("physics_summary") or {}
        summary = physics_summary.get("summary") or {}
        signal_models = _listify(physics_summary.get("signal_models"))
        power_models = _listify(physics_summary.get("power_models"))
        assumptions = physics_summary.get("assumptions") or {}
        answer = "Physics-informed SI/PI modeling is not available for this board yet."
        detail_parts = []
        if signal_models or power_models:
            answer = (
                f"Atlas modeled {len(signal_models)} critical signal net(s) and {len(power_models)} power net(s) "
                "from board geometry and configured material assumptions."
            )
            if summary.get("worst_impedance_mismatch_pct") is not None:
                detail_parts.append(
                    f"Worst impedance mismatch is {summary.get('worst_impedance_mismatch_pct')}%."
                )
            if summary.get("worst_voltage_drop_mv") is not None:
                detail_parts.append(
                    f"Worst estimated voltage drop is {summary.get('worst_voltage_drop_mv')} mV."
                )
            if assumptions.get("dielectric_er") is not None:
                detail_parts.append(
                    f"Model assumptions currently use dielectric er {assumptions.get('dielectric_er')} and dielectric height {assumptions.get('dielectric_height_mm')} mm."
                )
        return _make_response(
            intent,
            "Physics Integrity",
            answer,
            detail=" ".join(detail_parts) or "Atlas uses first-principles estimates so signal and power posture are tied to geometry, not only rule hits.",
            follow_ups=[
                "Which net looks worst in the model?",
                "How does this affect signoff?",
                "What should I fix first?",
            ],
            citations=[_source_to_citation(item) for item in _pick_top_risks(risk_sources, limit=3)],
            confidence=0.82,
        )

    if intent == "stackup":
        stackup_summary = context.get("stackup_summary") or {}
        concerns = _listify(stackup_summary.get("concerns"))
        return _make_response(
            "stackup",
            "Stackup and Return Path",
            (
                f"This board is being read as a {str(stackup_summary.get('style') or 'general').replace('_', ' ')} stackup "
                f"with {stackup_summary.get('layer_count', 0)} inferred layer(s) and {stackup_summary.get('reference_coverage_pct', 0)}% reference coverage."
            ),
            detail=concerns[0] if concerns else "Atlas is using inferred layer roles and reference coverage to reason about return-path quality.",
            follow_ups=[
                "Which nets are most exposed to stackup risk?",
                "How does this affect signoff?",
                "What should I fix first?",
            ],
            citations=[_source_to_citation(item) for item in _pick_top_risks(risk_sources, limit=3)],
            confidence=0.77,
        )

    if intent == "subsystem":
        subsystem_summary = context.get("subsystem_summary") or {}
        dominant_subsystem = subsystem_summary.get("dominant_subsystem") or "General"
        interaction_risks = _listify(subsystem_summary.get("interaction_risks"))
        return _make_response(
            "subsystem",
            "Subsystem Interaction",
            subsystem_summary.get("summary") or f"The dominant subsystem pressure is {dominant_subsystem}.",
            detail=(
                interaction_risks[0].get("message")
                if interaction_risks else
                "Atlas is using subsystem classification to look for architecture-level interaction risks, not only isolated rule hits."
            ),
            follow_ups=[
                "Which subsystem is driving the score most?",
                "What interaction should I validate next?",
                "Show me the strongest evidence",
            ],
            citations=[_source_to_citation(item) for item in _pick_top_risks(risk_sources, limit=3)],
            confidence=0.79,
        )

    domain_intents = {
        "power": ("Power Integrity Review", "power"),
        "signal": ("Signal and Return-Path Review", "signal"),
        "thermal": ("Thermal Review", "thermal"),
        "emi": ("EMI / EMC Review", "emi"),
        "manufacturing": ("Production Readiness Review", "manufacturability"),
        "safety": ("Safety and High-Voltage Review", "safety"),
    }
    if intent in domain_intents:
        title, domain = domain_intents[intent]
        matches = _pick_top_risks(risk_sources, limit=4, matcher=_domain_matcher(domain))
        board_domain_row = next((item for item in domain_rows if domain in _lower(item.get("label"))), None)
        headline = board_domain_row.get("headline") if board_domain_row else ""
        answer = (
            headline
            or (matches[0].get("message") if matches else f"{_titleize(domain)} is not the dominant board driver right now.")
        )
        detail = (
            f"Atlas is reading {dominant_domain if matches else _titleize(domain)} as a physical engineering question, not just a rule hit. The practical move is to inspect the cited region and determine whether layout, support structure, or placement is the real root cause."
        )
        action_item = matches[0] if matches else (top_actions[0] if top_actions else {})
        return _make_response(
            intent,
            title,
            answer,
            detail=detail,
            follow_ups=[
                "Show me the strongest evidence",
                "What should I fix first in this domain?",
                "What should I validate after the rerun?",
            ],
            citations=[_source_to_citation(item) for item in matches] or [_source_to_citation(item) for item in _pick_top_risks(risk_sources, limit=2)],
            actions=_action_payload(action_item, "heatmap") if action_item else {},
            confidence=0.8,
        )

    overview_citations = [_source_to_citation(item) for item in _pick_top_risks(risk_sources, limit=3)]
    subsystem_summary = context.get("subsystem_summary") or {}
    dominant_subsystem = subsystem_summary.get("dominant_subsystem")
    return _make_response(
        "overview",
        "Board Overview",
        context.get("summary")
        or context.get("posture")
        or f"Atlas currently sees {dominant_domain} as the main engineering driver on this board.",
        detail=(
            f"The board is currently at {context.get('score', 0)} / 100. "
            + (
                f"Atlas sees the strongest subsystem pressure in {dominant_subsystem}. "
                if dominant_subsystem else ""
            )
            + f"The most useful next step is to focus on {dominant_domain}, close the top action cleanly, and verify that the rerun improves trust as well as score."
        ),
        follow_ups=[
            "What should I fix first?",
            "Why is the score low?",
            "Am I signoff ready?",
        ],
        citations=overview_citations,
        actions=_action_payload(top_actions[0]) if top_actions else {},
        confidence=0.78,
    )


def _resolve_project_intent(prompt, history):
    lower = _lower(prompt)
    if _prompt_is_follow_up(prompt):
        return _history_last_intent(history) or "overview"
    mapping = [
        ("cam_portfolio", _keywords(["gerber", "cam", "fabrication package", "drill", "outline", "cam readiness"])),
        ("recurring_pattern", _keywords(["repeat", "recurring", "systemic", "pattern", "family"])),
        ("workspace_momentum", _keywords(["improv", "trend", "momentum", "better", "timeline"])),
        ("team_action", _keywords(["team", "next", "owner", "what should", "action"])),
        ("release_gate", _keywords(["gate", "signoff", "release", "ready", "approval"])),
        ("confidence", _keywords(["confidence", "trust", "defensible", "evidence"])),
        ("boards", _keywords(["which board", "board", "run", "contributing", "worst", "best"])),
    ]
    for intent, words in mapping:
        if any(word in lower for word in words):
            return intent
    return "overview"


def answer_project_question(prompt, context, history=None):
    context = context or {}
    history = history or []
    intent = _resolve_project_intent(prompt, history)
    trusted_focus = _listify(context.get("trusted_focus_items"))
    next_actions = _listify(context.get("next_actions"))
    run_summaries = _listify(context.get("run_summaries"))
    top_focus = trusted_focus[0] if trusted_focus else {}
    top_action = next_actions[0] if next_actions else {}
    cam_boards = _listify(context.get("cam_boards"))

    if intent == "cam_portfolio":
        if not cam_boards:
            return _make_response(
                "cam_portfolio",
                "CAM Portfolio",
                "This workspace does not currently include Gerber/CAM-backed review runs.",
                detail="Atlas only surfaces CAM portfolio guidance when at least one linked run includes a fabrication package import.",
                follow_ups=[
                    "Are we improving enough?",
                    "What should the team do next?",
                ],
                confidence=0.76,
            )
        ranked_cam = sorted(cam_boards, key=lambda item: _safe_float(item.get("readiness_score"), 0), reverse=True)
        weakest_cam = ranked_cam[-1]
        strongest_cam = ranked_cam[0]
        answer = (
            f"The workspace has {len(cam_boards)} CAM-backed run(s). "
            f"The strongest CAM package is {strongest_cam.get('name', 'Unknown')} ({str(strongest_cam.get('source_family') or 'generic_gerber').replace('_', ' ')}) "
            f"at {strongest_cam.get('readiness_score', 0)} / 100, while the weakest is {weakest_cam.get('name', 'Unknown')} "
            f"({str(weakest_cam.get('source_family') or 'generic_gerber').replace('_', ' ')}) at {weakest_cam.get('readiness_score', 0)} / 100."
        )
        detail = (
            f"{context.get('cam_ready_count', 0)} CAM package(s) are review ready. "
            + (
                f"The most urgent portfolio CAM gap is {weakest_cam.get('missing_signals', ['not yet classified'])[0]}."
                if weakest_cam.get("missing_signals") else
                "Atlas does not currently see a dominant CAM completeness gap."
            )
        )
        return _make_response(
            "cam_portfolio",
            "CAM Portfolio",
            answer,
            detail=detail,
            follow_ups=[
                "Which workspace issue is repeating most?",
                "What should the team do next?",
                "Are we improving enough for the next review gate?",
            ],
            confidence=0.8,
        )

    if intent == "recurring_pattern":
        return _make_response(
            "recurring_pattern",
            "Recurring Pattern",
            context.get("recurring_family_summary") or f"The strongest repeated issue family is {top_focus.get('category', 'not clear yet')}.",
            detail="Atlas is looking for issue families that survive across multiple runs, because those are usually process or architecture problems rather than one-off board mistakes.",
            follow_ups=[
                "Why does that pattern keep showing up?",
                "Which board is contributing most?",
                "What should the team do first?",
            ],
            citations=[_source_to_citation(top_focus)] if top_focus else [],
            confidence=0.83,
        )

    if intent == "workspace_momentum":
        return _make_response(
            "workspace_momentum",
            "Workspace Momentum",
            context.get("trend_summary") or context.get("momentum") or "No workspace momentum note is available yet.",
            detail=f"Health is currently {context.get('health_score', 0)} / 100 with average confidence at {context.get('average_confidence', 0)}. Atlas only treats that as real improvement if repeated issue pressure is actually dropping.",
            follow_ups=[
                "What changed most across the timeline?",
                "Are we review-gate ready?",
                "What is still holding the workspace back?",
            ],
            confidence=0.8,
        )

    if intent == "team_action":
        return _make_response(
            "team_action",
            "Next Team Action",
            top_action.get("recommendation") or top_action.get("message") or "No execution-plan action is available yet.",
            detail="Atlas wants the team to own one repeated pressure family at a time and verify the effect through the next linked rerun instead of spreading work across too many isolated findings.",
            follow_ups=[
                "Who should own this next?",
                "What should we validate after the rerun?",
                "What blocks the next review gate?",
            ],
            citations=[_source_to_citation(top_action)] if top_action else [],
            confidence=0.82,
        )

    if intent == "release_gate":
        return _make_response(
            "release_gate",
            "Release Gate",
            context.get("release_readiness") or "No release-readiness note is available yet.",
            detail="Atlas is reading the workspace as a review gate, so the decision depends on trend direction, repeated issue pressure, and confidence quality together.",
            follow_ups=[
                "What blocks the next review gate?",
                "Which repeated issue family matters most?",
                "Are we improving enough?",
            ],
            confidence=0.82,
        )

    if intent == "confidence":
        return _make_response(
            "confidence",
            "Workspace Trust",
            context.get("confidence_summary") or "No workspace confidence note is available yet.",
            detail="Atlas uses workspace confidence to judge whether recurring patterns are strong enough to drive planning or still need more validation before they shape release decisions.",
            follow_ups=[
                "Which pattern is the most defensible?",
                "What is repeating across this workspace?",
                "Are we review-gate ready?",
            ],
            confidence=0.76,
        )

    if intent == "boards":
        if run_summaries:
            ranked = sorted(run_summaries, key=lambda item: _safe_float(item.get("score"), 0))
            worst = ranked[0]
            best = ranked[-1]
            answer = f"The lowest-scoring linked run is {worst.get('name', 'Unknown')} at {worst.get('score', 0)} / 100, while the strongest is {best.get('name', 'Unknown')} at {best.get('score', 0)} / 100."
        else:
            answer = "No linked run summaries are available yet."
        return _make_response(
            "boards",
            "Board Contribution",
            answer,
            detail="Atlas uses board-to-board spread to decide whether the workspace problem is isolated to one revision or systemic across the design stream.",
            follow_ups=[
                "What is repeating across this workspace?",
                "Are we improving enough for the next gate?",
                "What should the team do next?",
            ],
            confidence=0.74,
        )

    return _make_response(
        "overview",
        "Workspace Overview",
        context.get("posture") or context.get("health_summary") or "No workspace overview is available yet.",
        detail="The most useful move is to isolate the strongest repeated issue family, assign ownership, and judge the next rerun by both risk reduction and confidence quality.",
        follow_ups=[
            "What is repeating across this workspace?",
            "Are we improving?",
            "What should the team do next?",
        ],
        confidence=0.77,
    )


def _resolve_compare_intent(prompt, history):
    lower = _lower(prompt)
    if _prompt_is_follow_up(prompt):
        return _history_last_intent(history) or "overview"
    mapping = [
        ("approval", _keywords(["approve", "approval", "signoff", "ready", "accept"])),
        ("regression", _keywords(["worse", "regress", "regression", "degraded", "bad"])),
        ("improvement", _keywords(["better", "improved", "improvement", "got better"])),
        ("top_change", _keywords(["change", "cluster", "difference", "moved"])),
        ("inspect_next", _keywords(["inspect", "next", "focus", "verify"])),
        ("domains", _keywords(["domain", "category", "impact", "moved most"])),
    ]
    for intent, words in mapping:
        if any(word in lower for word in words):
            return intent
    return "overview"


def answer_compare_question(prompt, context, history=None):
    context = context or {}
    history = history or []
    intent = _resolve_compare_intent(prompt, history)
    takeaways = _listify(context.get("takeaways"))
    focus_sources = _listify(context.get("focus_sources"))
    first_takeaway = takeaways[0] if takeaways else {}
    first_focus = focus_sources[0] if focus_sources else {}
    citations = [_source_to_citation(first_focus)] if first_focus else []

    if intent == "approval":
        return _make_response(
            "approval",
            "Approval Readiness",
            context.get("signoff_note") or "No signoff note is available yet.",
            detail="Atlas is treating this compare view as an approval gate. The key question is whether the changed findings are explainable, bounded, and worth the tradeoff against any improvements.",
            follow_ups=[
                "What got worse?",
                "Show the top change cluster",
                "What do I inspect next?",
            ],
            citations=citations,
            actions={"components": _listify(first_focus.get("components")), "nets": _listify(first_focus.get("nets"))} if first_focus else {},
            confidence=0.83,
        )

    if intent == "regression":
        return _make_response(
            "regression",
            "What Got Worse",
            context.get("root_cause") or "No dominant regression note is available yet.",
            detail="Atlas wants to confirm whether this regression is concentrated in one subsystem or spread across multiple domains before calling the new revision meaningfully worse.",
            follow_ups=[
                "Show the top change cluster",
                "What should I verify before approval?",
                "Can I approve this revision?",
            ],
            citations=citations,
            actions={"components": _listify(first_focus.get("components")), "nets": _listify(first_focus.get("nets"))} if first_focus else {},
            confidence=0.84,
        )

    if intent == "improvement":
        direction = _titleize(context.get("direction"), "Mixed")
        return _make_response(
            "improvement",
            "Improvement Readout",
            f"The current revision direction is {direction.lower()}, with score movement of {context.get('score_diff', 0)} points.",
            detail="Atlas treats score change as only one signal. The real question is whether the improved areas outweigh new risks and whether the movement is trustworthy at subsystem level.",
            follow_ups=[
                "What got worse?",
                "Can I approve this revision?",
                "Show the top change cluster",
            ],
            citations=citations,
            confidence=0.77,
        )

    if intent == "domains":
        domain_impacts = _listify(context.get("domain_impacts"))
        if domain_impacts:
            top_domain = domain_impacts[0]
            answer = f"{top_domain.get('domain', 'General')} moved the most with delta {top_domain.get('delta', 0)}."
        else:
            answer = "No domain movement summary is available yet."
        return _make_response(
            "domains",
            "Domain Movement",
            answer,
            detail="Atlas uses domain movement to separate broad engineering shifts from one concentrated revision cluster.",
            follow_ups=[
                "Why did that subsystem move?",
                "What got worse?",
                "What do I inspect next?",
            ],
            citations=citations,
            confidence=0.74,
        )

    if intent == "inspect_next":
        return _make_response(
            "inspect_next",
            "Next Inspection Step",
            first_takeaway.get("why") or context.get("next_move") or "No follow-up inspection step is available yet.",
            detail="Keep both revisions focused on the same subsystem so you can tell whether the movement is local, systemic, or an artifact of the comparison set.",
            follow_ups=[
                "Show the top change cluster",
                "Can I approve this revision?",
                "What got worse?",
            ],
            citations=citations,
            actions={"components": _listify(first_focus.get("components")), "nets": _listify(first_focus.get("nets"))} if first_focus else {},
            confidence=0.8,
        )

    if intent == "top_change":
        return _make_response(
            "top_change",
            "Top Change Cluster",
            first_takeaway.get("why") or context.get("root_cause") or "No dominant revision cluster is available yet.",
            detail="Atlas is trying to reduce the compare story to the subsystem change that best explains the score and risk movement between revisions.",
            follow_ups=[
                "What got worse?",
                "Can I approve this revision?",
                "What should I inspect next?",
            ],
            citations=citations,
            actions={"components": _listify(first_focus.get("components")), "nets": _listify(first_focus.get("nets"))} if first_focus else {},
            confidence=0.82,
        )

    return _make_response(
        "overview",
        "Comparison Overview",
        context.get("posture") or "No comparison overview is available yet.",
        detail="The most useful compare question is whether the changed findings form one coherent subsystem story that is strong enough to guide approval or rejection.",
        follow_ups=[
            "What got worse?",
            "Can I approve this revision?",
            "Show the top change cluster",
        ],
        citations=citations,
        confidence=0.76,
    )


def answer_atlas_question(page_type, prompt, context=None, history=None):
    normalized_page = _lower(page_type)
    if normalized_page == "board":
        return answer_board_question(prompt, context, history)
    if normalized_page == "project":
        return answer_project_question(prompt, context, history)
    if normalized_page == "compare":
        return answer_compare_question(prompt, context, history)
    return _make_response(
        "overview",
        "Atlas Intelligence",
        "Atlas could not determine the current review surface for this question.",
        detail="Try asking from a board, compare, or Silicore workspace page with active context.",
        follow_ups=[],
        confidence=0.5,
    )
