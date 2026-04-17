from engine.evaluation_backend import evaluate_external_suite, summarize_evaluation_history
from engine.job_store import create_job, get_job, summarize_jobs, update_job
from engine.signoff_engine import evaluate_signoff_gate


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _sort_runs(runs):
    return sorted(runs or [], key=lambda item: str(item.get("created_at") or ""))


def create_signoff_packet(context):
    top_actions = context.get("top_actions") or context.get("next_actions") or []
    validation_plan = context.get("validation_plan") or []
    return {
        "title": "Signoff Packet Draft",
        "summary": context.get("release_note") or context.get("health_summary") or "No signoff summary is available yet.",
        "dominant_domain": context.get("dominant_domain") or context.get("posture") or "General",
        "fix_first": top_actions[:3],
        "validation_plan": validation_plan[:4],
        "board_or_project": context.get("board_name") or context.get("project_name") or "Workspace",
    }


def compare_latest_runs(context):
    runs = _sort_runs(context.get("run_summaries") or [])
    if len(runs) < 2:
        return {
            "status": "insufficient_runs",
            "summary": "At least two linked runs are required for comparison.",
        }
    baseline = runs[-2]
    latest = runs[-1]
    return {
        "status": "ready",
        "baseline": baseline,
        "latest": latest,
        "score_delta": round(float(latest.get("score", 0) or 0) - float(baseline.get("score", 0) or 0), 1),
        "risk_delta": _safe_int(latest.get("risk_count"), 0) - _safe_int(baseline.get("risk_count"), 0),
        "summary": f"Compared {baseline.get('name', 'baseline')} against {latest.get('name', 'latest')}.",
    }


def open_high_confidence_findings(context, domain=None, confidence_floor=0.8):
    items = []
    for risk in context.get("risk_sources") or []:
        confidence = float(risk.get("confidence", risk.get("confidence_score", 0)) or 0)
        risk_domain = str(risk.get("domain") or risk.get("category") or "").lower()
        if confidence < confidence_floor:
            continue
        if domain and domain.lower() not in risk_domain:
            continue
        items.append(risk)
    return {
        "status": "ready",
        "count": len(items),
        "domain": domain or "all",
        "items": items[:8],
    }


def queue_evaluation(fixtures_dir="fixtures", config="custom_config.json", actor_user_id=None):
    job = create_job(
        "evaluation_suite",
        payload={"fixtures_dir": fixtures_dir, "config": config},
        actor_user_id=actor_user_id,
    )
    return {"job": get_job(job["job_id"]), "result": {"status": "queued"}}


def queue_external_validation(samples_dir, config="custom_config.json", label=None, actor_user_id=None):
    job = create_job(
        "external_evaluation_suite",
        payload={"samples_dir": samples_dir, "config": config, "label": label or "External Validation"},
        actor_user_id=actor_user_id,
    )
    return {"job": get_job(job["job_id"]), "result": {"status": "queued"}}


def queue_signoff_packet(context, actor_user_id=None):
    job = create_job(
        "signoff_packet",
        payload={"context": context or {}},
        actor_user_id=actor_user_id,
    )
    return {"job": get_job(job["job_id"]), "result": {"status": "queued"}}


def evaluate_signoff_readiness(context):
    result = context or {}
    signoff_gate = result.get("signoff_gate") or {}
    if signoff_gate:
        return {
            "status": "ready",
            "summary": signoff_gate.get("summary") or "Signoff gate is available.",
            "decision": signoff_gate.get("decision"),
            "release_score": signoff_gate.get("release_score"),
            "blockers": signoff_gate.get("blockers") or [],
            "next_checks": signoff_gate.get("next_checks") or [],
        }

    gate = evaluate_signoff_gate(result)
    return {
        "status": "ready",
        "summary": gate.get("summary") or "Signoff gate is available.",
        "decision": gate.get("decision"),
        "release_score": gate.get("release_score"),
        "blockers": gate.get("blockers") or [],
        "next_checks": gate.get("next_checks") or [],
    }


def inspect_parser_trust(context):
    cam_summary = context.get("cam_summary") or {}
    parser_confidence = (context.get("parser_confidence") or {}).get("score", 0)
    signoff_gate = context.get("signoff_gate") or {}
    return {
        "status": "ready",
        "summary": (
            f"Parser confidence is {parser_confidence} / 100 and CAM readiness is {cam_summary.get('readiness_score', 0)} / 100."
            if cam_summary.get("active")
            else f"Parser confidence is {parser_confidence} / 100."
        ),
        "parser_confidence": parser_confidence,
        "trust_call": cam_summary.get("trust_call") or ("trusted" if parser_confidence >= 80 else "parser_watch"),
        "missing_signals": cam_summary.get("missing_signals") or [],
        "fabrication_blockers": cam_summary.get("fabrication_blockers") or [],
        "parser_warnings": cam_summary.get("parser_warnings") or [],
        "release_score": signoff_gate.get("release_score"),
    }


def retry_failed_jobs(limit=5):
    from engine.job_runner import process_queued_jobs

    summary = summarize_jobs(limit=100)
    retried = []
    for job in summary.get("jobs", []):
        if len(retried) >= int(limit or 5):
            break
        if str(job.get("status") or "").lower() != "failed":
            continue
        attempts = int(job.get("attempt_count") or 0)
        max_attempts = int(job.get("max_attempts") or 0)
        if attempts >= max_attempts:
            continue
        update_job(job["job_id"], status="queued", error_text=job.get("error_text"))
        retried.append(get_job(job["job_id"]))
    processed = process_queued_jobs(limit=len(retried), worker_id="atlas-retry") if retried else []
    return {"status": "ready", "retried_count": len(retried), "processed": processed}


def run_tool_action(action_name, context=None, actor_user_id=None, params=None):
    context = context or {}
    params = params or {}

    if action_name == "generate_signoff_packet":
        if params.get("async"):
            return queue_signoff_packet(context, actor_user_id=actor_user_id)
        packet = create_signoff_packet(context)
        job = create_job("signoff_packet", payload={"context_type": context.get("board_name") or context.get("project_name")}, actor_user_id=actor_user_id, status="completed")
        update_job(job["job_id"], status="completed", result=packet)
        return {"job": get_job(job["job_id"]), "result": packet}

    if action_name == "compare_latest_runs":
        result = compare_latest_runs(context)
        job = create_job("compare_latest_runs", payload={"project_name": context.get("project_name")}, actor_user_id=actor_user_id)
        update_job(job["job_id"], status="completed", result=result)
        return {"job": get_job(job["job_id"]), "result": result}

    if action_name == "open_high_confidence_findings":
        result = open_high_confidence_findings(
            context,
            domain=params.get("domain"),
            confidence_floor=float(params.get("confidence_floor", 0.8)),
        )
        job = create_job("open_high_confidence_findings", payload=params, actor_user_id=actor_user_id)
        update_job(job["job_id"], status="completed", result=result)
        return {"job": get_job(job["job_id"]), "result": result}

    if action_name == "run_fixture_evaluation":
        return queue_evaluation(
            fixtures_dir=params.get("fixtures_dir", "fixtures"),
            config=params.get("config", "custom_config.json"),
            actor_user_id=actor_user_id,
        )

    if action_name == "run_external_validation":
        samples_dir = params.get("samples_dir") or context.get("samples_dir")
        if not samples_dir:
            return {"error": "samples_dir is required for external validation."}
        if params.get("async", True):
            return queue_external_validation(
                samples_dir=samples_dir,
                config=params.get("config", "custom_config.json"),
                label=params.get("label") or context.get("label"),
                actor_user_id=actor_user_id,
            )
        result = evaluate_external_suite(
            samples_dir,
            config=params.get("config", "custom_config.json"),
            label=params.get("label") or context.get("label"),
        )
        job = create_job("external_evaluation_suite", payload={"samples_dir": samples_dir}, actor_user_id=actor_user_id, status="completed")
        update_job(job["job_id"], status="completed", result=result)
        return {"job": get_job(job["job_id"]), "result": result}

    if action_name == "evaluate_signoff_gate":
        result = evaluate_signoff_readiness(context)
        job = create_job("evaluate_signoff_gate", payload={"context_type": context.get("board_name") or context.get("project_name")}, actor_user_id=actor_user_id)
        update_job(job["job_id"], status="completed", result=result)
        return {"job": get_job(job["job_id"]), "result": result}

    if action_name == "inspect_parser_trust":
        result = inspect_parser_trust(context)
        job = create_job("inspect_parser_trust", payload={"context_type": context.get("board_name") or context.get("project_name")}, actor_user_id=actor_user_id)
        update_job(job["job_id"], status="completed", result=result)
        return {"job": get_job(job["job_id"]), "result": result}

    if action_name == "review_validation_history":
        result = summarize_evaluation_history(limit=_safe_int(params.get("limit"), 20))
        job = create_job("review_validation_history", payload={"limit": _safe_int(params.get("limit"), 20)}, actor_user_id=actor_user_id)
        update_job(job["job_id"], status="completed", result=result)
        return {"job": get_job(job["job_id"]), "result": result}

    if action_name == "retry_failed_jobs":
        result = retry_failed_jobs(limit=_safe_int(params.get("limit"), 5))
        job = create_job("retry_failed_jobs", payload={"limit": _safe_int(params.get("limit"), 5)}, actor_user_id=actor_user_id, status="completed")
        update_job(job["job_id"], status="completed", result=result)
        return {"job": get_job(job["job_id"]), "result": result}

    job = create_job("unknown_action", payload={"action_name": action_name, "params": params}, actor_user_id=actor_user_id)
    update_job(job["job_id"], status="failed", error_text=f"Unknown Atlas tool action: {action_name}")
    return {"job": get_job(job["job_id"]), "error": f"Unknown Atlas tool action: {action_name}"}
