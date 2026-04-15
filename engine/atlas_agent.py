import json
import os
from urllib import error, request

from engine.atlas_engine import answer_atlas_question


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


def _build_messages(page_type, prompt, context, history, deterministic_answer):
    system_prompt = (
        "You are Atlas Intelligence, a grounded PCB engineering assistant inside Silicore Nexus. "
        "Answer only from the supplied engineering context, deterministic Atlas answer, and thread history. "
        "Do not invent board facts, parser output, nets, components, measurements, or risks that are not present. "
        "If evidence is weak or missing, say so clearly. "
        "Return strict JSON with keys: title, answer, detail, follow_ups, confidence. "
        "follow_ups must be an array of short engineering follow-up questions. "
        "confidence must be a number from 0 to 1."
    )
    user_prompt = (
        f"Page type: {page_type}\n"
        f"User question: {prompt}\n\n"
        f"Deterministic Atlas answer:\n{_safe_json(deterministic_answer)}\n\n"
        f"Context:\n{_safe_json(context)}\n\n"
        f"Recent thread:\n{_safe_json(history[-8:])}\n\n"
        "Respond with grounded engineering guidance only."
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _call_openai_json(messages, config):
    payload = {
        "model": config["model"],
        "temperature": 0.2,
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
        content = data["choices"][0]["message"]["content"]
        return json.loads(_strip_fences(content))


def _merge_llm_answer(deterministic_answer, llm_answer):
    merged = dict(deterministic_answer or {})
    merged["title"] = llm_answer.get("title") or merged.get("title") or "Atlas Intelligence"
    merged["answer"] = llm_answer.get("answer") or merged.get("answer") or "No answer available."
    merged["detail"] = llm_answer.get("detail") or merged.get("detail") or ""
    merged["follow_ups"] = llm_answer.get("follow_ups") or merged.get("follow_ups") or []
    merged["confidence"] = llm_answer.get("confidence", merged.get("confidence", 0.78))
    merged["mode"] = "llm_agent"
    return merged


def answer_atlas_with_agent(page_type, prompt, context=None, history=None):
    context = context or {}
    history = history or []
    deterministic_answer = answer_atlas_question(page_type, prompt, context=context, history=history)

    config = _load_agent_config()
    if not config["enabled"]:
        deterministic_answer["mode"] = "deterministic"
        return deterministic_answer

    try:
        messages = _build_messages(page_type, prompt, context, history, deterministic_answer)
        llm_answer = _call_openai_json(messages, config)
        return _merge_llm_answer(deterministic_answer, llm_answer)
    except (error.URLError, error.HTTPError, TimeoutError, KeyError, ValueError, json.JSONDecodeError):
        deterministic_answer["mode"] = "deterministic"
        return deterministic_answer
