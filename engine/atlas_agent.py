import json
import os
from urllib import error, request

from engine.atlas_engine import answer_atlas_question
from engine.atlas_tools import run_tool_action
from engine.atlas_workflow import build_workflow_plan
from engine.db import persist_atlas_agent_run


def _safe_json(data):
    try:
        return json.dumps(data, indent=2, sort_keys=True)
    except Exception:
        return "{}"


def _strip_fences(text):
    value = str(text or "").strip()
    if value.startswith("```"):
        parts = value.split("\n")
        if len(parts) >= 3:
            value = "\n".join(parts[1:-1]).strip()
    return value


def _load_agent_config():
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("SILICORE_ATLAS_API_KEY")
    base_url = (os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("SILICORE_ATLAS_MODEL") or "gpt-4.1-mini"
    return {
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
        "enabled": bool(api_key),
    }


def _build_agent_plan(page_type, prompt, context, history, deterministic_answer):
    plan = build_workflow_plan(page_type, prompt, context=context) or []
    lowered = str(prompt or "").lower()
    if page_type == "board" and any(token in lowered for token in ["physics", "model", "impedance", "ir drop", "parser", "trust"]):
        plan = [
            {"action_name": "inspect_parser_trust", "reason": "Atlas should ground trust questions in parser and CAM readiness before answering.", "params": {}},
            {"action_name": "evaluate_signoff_gate", "reason": "Atlas should refresh the release gate when the user asks about parser trust or physical readiness.", "params": {}},
        ] + plan

    seen = set()
    deduped = []
    for step in plan:
        key = (step.get("action_name"), json.dumps(step.get("params") or {}, sort_keys=True))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(step)

    if not deduped and deterministic_answer.get("intent") == "signoff":
        deduped.append(
            {
                "action_name": "evaluate_signoff_gate",
                "reason": "Atlas wants a release-gate readout before answering signoff questions.",
                "params": {},
            }
        )
    return deduped[:4]


def _execute_agent_plan(plan, context, actor_user_id=None):
    working_context = dict(context or {})
    results = []
    for index, step in enumerate(plan, start=1):
        tool_result = run_tool_action(
            step["action_name"],
            context=working_context,
            actor_user_id=actor_user_id,
            params=step.get("params") or {},
        )
        compact = {
            "step": index,
            "action_name": step["action_name"],
            "reason": step.get("reason") or "",
            "params": step.get("params") or {},
            "result": tool_result.get("result"),
            "job": tool_result.get("job"),
            "error": tool_result.get("error"),
            "status": "failed" if tool_result.get("error") else "completed",
        }
        results.append(compact)
        if step["action_name"] == "evaluate_signoff_gate" and compact["result"]:
            working_context["signoff_gate"] = compact["result"]
        if step["action_name"] == "open_high_confidence_findings" and compact["result"]:
            working_context["focused_findings"] = compact["result"].get("items") or []
    return results, working_context


def _build_messages(page_type, prompt, context, history, deterministic_answer, plan, results):
    system_prompt = (
        "You are Atlas Intelligence, the core engineering intelligence engine inside Silicore. "
        "Behave like a senior hardware engineer reviewing a design beside the user: grounded, direct, predictive, and action-oriented. "
        "Reason with three layers in mind: deterministic engineering constraints, contextual system interaction, and adaptive learning from reruns and outcomes. "
        "Preserve continuity from the active review thread so Atlas feels like it remembers what the user is trying to prove, fix, or validate. "
        "Answer only from the supplied engineering context, deterministic Atlas answer, workflow plan, tool results, and thread history. "
        "Do not invent board facts, parser output, nets, components, measurements, or risks. "
        "Prioritize what is most likely to fail, why it matters in the real world, what should be fixed first, and what should be validated next. "
        "When possible, make the answer proactive instead of passive: recommend the next engineering move, the validation step after it, and the tradeoff to watch. "
        "Return strict JSON with keys: title, answer, detail, follow_ups, confidence."
    )
    user_prompt = (
        f"Page type: {page_type}\n"
        f"User question: {prompt}\n\n"
        f"Deterministic Atlas answer:\n{_safe_json(deterministic_answer)}\n\n"
        f"Context:\n{_safe_json(context)}\n\n"
        f"Agent plan:\n{_safe_json(plan)}\n\n"
        f"Executed tool results:\n{_safe_json(results)}\n\n"
        f"Recent thread:\n{_safe_json(history[-8:])}\n\n"
        "Use the executed tool results when they materially improve the answer."
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _call_openai_json(messages, config):
    payload = {
        "model": config["model"],
        "temperature": 0.15,
        "response_format": {"type": "json_object"},
        "messages": messages,
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"{config['base_url']}/chat/completions",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key']}",
        },
    )
    with request.urlopen(req, timeout=20) as response:
        data = json.loads(response.read().decode("utf-8"))
        return json.loads(_strip_fences(data["choices"][0]["message"]["content"]))


def _merge_answer(deterministic_answer, llm_answer, plan, results, mode):
    merged = dict(deterministic_answer or {})
    merged["title"] = llm_answer.get("title") or merged.get("title") or "Atlas Intelligence"
    merged["answer"] = llm_answer.get("answer") or merged.get("answer") or "No answer available."
    merged["detail"] = llm_answer.get("detail") or merged.get("detail") or ""
    merged["follow_ups"] = llm_answer.get("follow_ups") or merged.get("follow_ups") or []
    merged["confidence"] = llm_answer.get("confidence", merged.get("confidence", 0.78))
    merged["mode"] = mode
    merged["agent_plan"] = plan
    merged["agent_results"] = results
    merged["agent_trace"] = [
        {
            "step": item.get("step"),
            "label": str(item.get("action_name") or "").replace("_", " "),
            "status": item.get("status"),
            "summary": item.get("error") or ((item.get("result") or {}).get("summary")) or ((item.get("job") or {}).get("status")) or "completed",
        }
        for item in results
    ]
    return merged


def answer_atlas_with_agent(page_type, prompt, context=None, history=None, actor_user_id=None):
    context = context or {}
    history = history or []
    deterministic_answer = answer_atlas_question(page_type, prompt, context=context, history=history)
    plan = _build_agent_plan(page_type, prompt, context, history, deterministic_answer)
    results, enriched_context = _execute_agent_plan(plan, context, actor_user_id=actor_user_id)

    config = _load_agent_config()
    model_mode = "llm_agent" if config["enabled"] else "deterministic_agent"
    final_answer = dict(deterministic_answer)

    if config["enabled"]:
        try:
            messages = _build_messages(page_type, prompt, enriched_context, history, deterministic_answer, plan, results)
            llm_answer = _call_openai_json(messages, config)
            final_answer = _merge_answer(deterministic_answer, llm_answer, plan, results, model_mode)
        except (error.URLError, error.HTTPError, TimeoutError, KeyError, ValueError, json.JSONDecodeError):
            final_answer = _merge_answer(deterministic_answer, {}, plan, results, "deterministic_agent")
    else:
        final_answer = _merge_answer(deterministic_answer, {}, plan, results, model_mode)

    thread_key = f"{page_type}::{str(context.get('project_id') or context.get('run_id') or context.get('board_name') or context.get('project_name') or 'atlas').lower()}"
    persist_atlas_agent_run(thread_key, page_type, prompt, plan, results, model_mode=final_answer.get("mode", model_mode), status="completed")
    return final_answer
