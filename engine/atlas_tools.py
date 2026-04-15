from engine.evaluation_backend import run_evaluation_job
from engine.job_store import create_job, get_job, update_job


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
    result = run_evaluation_job(job["job_id"], fixtures_dir=fixtures_dir, config=config)
    return {"job": get_job(job["job_id"]), "result": result}


def run_tool_action(action_name, context=None, actor_user_id=None, params=None):
    context = context or {}
    params = params or {}

    if action_name == "generate_signoff_packet":
        packet = create_signoff_packet(context)
        job = create_job("signoff_packet", payload={"context_type": context.get("board_name") or context.get("project_name")}, actor_user_id=actor_user_id)
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

    job = create_job("unknown_action", payload={"action_name": action_name, "params": params}, actor_user_id=actor_user_id)
    update_job(job["job_id"], status="failed", error_text=f"Unknown Atlas tool action: {action_name}")
    return {"job": get_job(job["job_id"]), "error": f"Unknown Atlas tool action: {action_name}"}
