from engine.atlas_tools import run_tool_action


def _lower(value):
    return str(value or "").strip().lower()


def _contains_any(text, keywords):
    lowered = _lower(text)
    return any(keyword in lowered for keyword in keywords)


def build_workflow_plan(page_type, prompt, context=None):
    context = context or {}
    lowered = _lower(prompt)
    steps = []

    if _contains_any(lowered, ["signoff packet", "signoff report", "approval packet", "review packet"]):
        steps.append(
            {
                "action_name": "generate_signoff_packet",
                "reason": "User asked for a signoff-style output from the current engineering context.",
                "params": {"async": True},
            }
        )

    if page_type == "board" and _contains_any(lowered, ["signoff", "release readiness", "ready to ship", "ready for approval", "blocked"]):
        steps.append(
            {
                "action_name": "evaluate_signoff_gate",
                "reason": "User asked whether the current board is actually ready for signoff or what is blocking release.",
                "params": {},
            }
        )

    if page_type == "project" and _contains_any(lowered, ["compare latest", "latest runs", "compare revisions", "latest comparison"]):
        steps.append(
            {
                "action_name": "compare_latest_runs",
                "reason": "User asked Atlas to compare the most recent linked workspace runs.",
                "params": {},
            }
        )

    if _contains_any(lowered, ["high confidence", "trusted findings", "strongest evidence", "only the confident findings"]):
        domain = None
        for candidate in ["power", "signal", "thermal", "emi", "safety", "manufacturing"]:
            if candidate in lowered:
                domain = candidate
                break
        steps.append(
            {
                "action_name": "open_high_confidence_findings",
                "reason": "User asked for a narrowed view of stronger, more defensible findings.",
                "params": {"domain": domain, "confidence_floor": 0.8},
            }
        )

    if _contains_any(lowered, ["evaluate fixtures", "evaluation suite", "benchmark", "calibration", "regression suite"]):
        steps.append(
            {
                "action_name": "run_fixture_evaluation",
                "reason": "User asked for a backend evaluation or calibration pass over the fixture set.",
                "params": {},
            }
        )

    if _contains_any(lowered, ["external validation", "validate this package", "validate this export", "outside package", "vendor drop"]):
        steps.append(
            {
                "action_name": "run_external_validation",
                "reason": "User asked Atlas to validate an external fabrication package instead of the internal fixture suite.",
                "params": {"async": True},
            }
        )

    if _contains_any(lowered, ["parser trust", "parser confidence", "fabrication trust", "cam readiness", "can i trust this import"]):
        steps.append(
            {
                "action_name": "inspect_parser_trust",
                "reason": "User asked whether the imported board/package is trustworthy enough for engineering or fabrication review.",
                "params": {},
            }
        )

    if _contains_any(lowered, ["benchmark trend", "validation trend", "history of validation", "calibration trend"]):
        steps.append(
            {
                "action_name": "review_validation_history",
                "reason": "User asked for parser and benchmark performance over time instead of one current summary.",
                "params": {"limit": 20},
            }
        )

    if _contains_any(lowered, ["retry failed jobs", "re-run failed jobs", "clear failed jobs"]):
        steps.append(
            {
                "action_name": "retry_failed_jobs",
                "reason": "User asked Atlas to retry failed operational jobs from the runtime queue.",
                "params": {"limit": 5},
            }
        )

    if page_type == "project" and _contains_any(lowered, ["release plan", "signoff plan", "approval plan"]):
        steps.extend(
            [
                {
                    "action_name": "compare_latest_runs",
                    "reason": "Atlas should first compare the newest linked workspace runs to understand release direction.",
                    "params": {},
                },
                {
                    "action_name": "generate_signoff_packet",
                    "reason": "After comparing the latest runs, Atlas should prepare a signoff-ready packet draft.",
                    "params": {"async": True},
                },
            ]
        )

    return steps


def run_workflow_plan(page_type, prompt, context=None, actor_user_id=None):
    plan = build_workflow_plan(page_type, prompt, context=context)
    if not plan:
        return []

    results = []
    for step in plan:
        tool_result = run_tool_action(
            step["action_name"],
            context=context or {},
            actor_user_id=actor_user_id,
            params=step.get("params") or {},
        )
        results.append(
            {
                "action_name": step["action_name"],
                "reason": step["reason"],
                "params": step.get("params") or {},
                "result": tool_result.get("result"),
                "job": tool_result.get("job"),
                "error": tool_result.get("error"),
            }
        )
    return results
