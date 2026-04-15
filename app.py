import json
import os
import re
from collections import defaultdict
from engine.insight_engine import generate_comparison_insights

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

from engine.config_loader import parse_config_form, save_config
from engine.dashboard_storage import get_recent_runs
from engine.project_store import (
    add_run_to_project,
    create_project,
    delete_project,
    get_project,
    list_projects,
)
from engine.services.analysis_service import (
    FORMAT_READINESS,
    analyze_project_files,
    analyze_single_board,
    get_dashboard_config,
)

app = Flask(__name__)
app.secret_key = "silicore-dev-secret"

UPLOAD_FOLDER = "dashboard_uploads"
RUNS_FOLDER = "dashboard_runs"
PROJECTS_FOLDER = "dashboard_projects"
CONFIG_PATH = "custom_config.json"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RUNS_FOLDER, exist_ok=True)
os.makedirs(PROJECTS_FOLDER, exist_ok=True)


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


def _normalize_compare_text(value):
    return " ".join(str(value or "").strip().lower().split())


def _normalize_compare_message(message):
    text = _normalize_compare_text(message)
    for old in ["warning: ", "issue: ", "risk: "]:
        text = text.replace(old, "")
    return text


def _normalize_string_list(values):
    if not isinstance(values, list):
        return []

    normalized = []
    for value in values:
        cleaned = str(value or "").strip()
        if cleaned:
            normalized.append(cleaned)

    return sorted(set(normalized))


def _build_comparison_signatures(risk):
    category = _normalize_compare_text(risk.get("category") or "unknown")
    rule_id = _normalize_compare_text(risk.get("rule_id") or "unknown_rule")
    message = _normalize_compare_message(risk.get("message"))
    components = "|".join(_normalize_string_list(risk.get("components")))
    nets = "|".join(_normalize_string_list(risk.get("nets")))

    base_signature = f"{category}|{rule_id}|{message}"
    signature = f"{base_signature}|c:{components}|n:{nets}"

    return {
        "signature": signature,
        "base_signature": base_signature,
        "normalized_message": message,
    }


def _severity_rank(severity):
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return order.get(str(severity).lower(), 4)


def _format_category_name(category):
    if not category:
        return "Uncategorized"
    return str(category).replace("_", " ").title()


def _format_metric_key(key):
    if not key:
        return "Metric"
    return str(key).replace("_", " ").title()


def _safe_json_load(file_path, default=None):
    if default is None:
        default = {}
    if not os.path.isfile(file_path):
        return default
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return default


def _prepare_grouped_risks(risks):
    grouped = defaultdict(list)
    for risk in risks or []:
        category = risk.get("category", "uncategorized")
        grouped[category].append(risk)

    grouped_sections = []
    for category, items in grouped.items():
        sorted_items = sorted(
            items,
            key=lambda item: (_severity_rank(item.get("severity")), item.get("message", "")),
        )
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for item in sorted_items:
            sev = str(item.get("severity", "")).lower()
            if sev in severity_counts:
                severity_counts[sev] += 1

        grouped_sections.append(
            {
                "key": category,
                "title": _format_category_name(category),
                "risks": sorted_items,
                "count": len(sorted_items),
                "severity_counts": severity_counts,
            }
        )

    grouped_sections.sort(
        key=lambda section: (
            min([_severity_rank(risk.get("severity")) for risk in section["risks"]] or [99]),
            section["title"],
        )
    )
    return grouped_sections


def _prepare_top_issues(risks, limit=3):
    sorted_risks = sorted(
        risks or [],
        key=lambda item: (
            _severity_rank(item.get("severity")),
            item.get("category", ""),
            item.get("message", ""),
        ),
    )
    return sorted_risks[:limit]


def _build_health_summary(score, risks):
    score_value = _safe_float(score, 0.0)
    risk_count = len(risks or [])
    critical_count = sum(
        1 for risk in (risks or [])
        if str(risk.get("severity", "")).lower() == "critical"
    )
    high_count = sum(
        1 for risk in (risks or [])
        if str(risk.get("severity", "")).lower() == "high"
    )

    if score_value >= 8.5 and critical_count == 0:
        return {
            "title": "Strong board health",
            "summary": "This board looks solid overall. Remaining issues appear targeted rather than systemic.",
        }
    if critical_count > 0:
        return {
            "title": "Critical review needed",
            "summary": "At least one critical issue is present. This board should be reviewed before release decisions.",
        }
    if high_count >= 3 or score_value < 5.0:
        return {
            "title": "Needs engineering attention",
            "summary": "This board has multiple high-impact issues that could affect implementation quality or reliability.",
        }
    if risk_count == 0:
        return {
            "title": "No issues detected",
            "summary": "No findings were produced under the current ruleset and configuration.",
        }
    return {
        "title": "Moderate review recommended",
        "summary": "The board is workable, but there are still a few meaningful issues worth cleaning up.",
    }


def _build_project_health_summary(project_result):
    project_summary = project_result.get("project_summary", {}) or {}
    boards = project_result.get("boards", []) or []
    average_score = _safe_float(project_summary.get("average_score", 0), 0.0)
    best_score = _safe_float(project_summary.get("best_score", 0), 0.0)
    worst_score = _safe_float(project_summary.get("worst_score", 0), 0.0)

    if not boards:
        return {
            "title": "No boards analyzed",
            "summary": "Upload a project set to compare boards and see project-wide engineering health.",
        }
    if average_score >= 8.0 and worst_score >= 7.0:
        return {
            "title": "Strong project baseline",
            "summary": "The uploaded boards are consistently healthy and do not show major spread in quality.",
        }
    if worst_score < 5.0 and best_score >= 8.0:
        return {
            "title": "Large project quality spread",
            "summary": "Some boards are in strong shape while at least one design needs much deeper engineering attention.",
        }
    if average_score < 6.0:
        return {
            "title": "Project review recommended",
            "summary": "The overall project trend shows enough risk that broader cleanup is worth doing before release confidence increases.",
        }
    return {
        "title": "Mixed but manageable",
        "summary": "The project has a workable baseline, but board quality is not yet consistently strong across the set.",
    }


def _build_score_breakdown(result):
    score_explanation = result.get("score_explanation") or {}
    severity_totals = score_explanation.get("severity_totals") or {}
    category_totals = score_explanation.get("category_totals") or {}
    penalties = score_explanation.get("detailed_penalties") or []

    severity_rows = []
    for severity in ["critical", "high", "medium", "low"]:
        total = _safe_float(severity_totals.get(severity), 0.0)
        count = sum(
            1 for item in penalties
            if str(item.get("severity", "")).lower() == severity
        )
        severity_rows.append(
            {
                "severity": severity,
                "label": severity.title(),
                "count": count,
                "total_penalty": round(total, 2),
            }
        )

    category_rows = []
    for category, penalty in sorted(category_totals.items()):
        category_rows.append(
            {
                "category": category,
                "label": _format_category_name(category),
                "penalty": round(_safe_float(penalty, 0.0), 2),
            }
        )

    return {
        "start_score": round(_safe_float(score_explanation.get("start_score", 10.0), 10.0), 2),
        "final_score": round(_safe_float(score_explanation.get("final_score", result.get("score", 0)), 0.0), 2),
        "total_penalty": round(_safe_float(score_explanation.get("total_penalty", result.get("total_penalty", 0)), 0.0), 2),
        "severity_rows": severity_rows,
        "category_rows": category_rows,
    }


def _flatten_config_snapshot(config_snapshot):
    if not isinstance(config_snapshot, dict):
        return []

    ordered_sections = [
        "layout",
        "power",
        "signal",
        "thermal",
        "emi",
        "score",
        "rules",
    ]

    flat = []

    def _append_items(section_name, section_data, prefix=""):
        if not isinstance(section_data, dict):
            return

        for key, value in section_data.items():
            label = f"{prefix}{_format_metric_key(key)}"
            if isinstance(value, dict):
                _append_items(section_name, value, prefix=f"{label} · ")
            else:
                if isinstance(value, list):
                    display_value = ", ".join(str(item) for item in value) if value else "None"
                elif isinstance(value, bool):
                    display_value = "Yes" if value else "No"
                else:
                    display_value = value

                flat.append(
                    {
                        "section": _format_category_name(section_name),
                        "key": key,
                        "label": label,
                        "value": display_value,
                    }
                )

    used = set()
    for section in ordered_sections:
        if section in config_snapshot:
            used.add(section)
            _append_items(section, config_snapshot.get(section))

    for section, value in config_snapshot.items():
        if section in used:
            continue
        _append_items(section, value)

    return flat


def _build_analysis_context(result):
    result = result or {}
    context = result.get("analysis_context") or {}

    config_snapshot = (
        context.get("config_snapshot")
        or result.get("config_snapshot")
        or {}
    )

    board_name = (
        context.get("board_name")
        or result.get("filename")
        or result.get("board_name")
        or "Unknown Board"
    )

    performed_at = (
        context.get("timestamp")
        or result.get("created_at")
        or result.get("timestamp")
        or "Unknown"
    )

    return {
        "board_name": board_name,
        "performed_at": performed_at,
        "config_snapshot": config_snapshot,
        "config_rows": _flatten_config_snapshot(config_snapshot),
        "score_breakdown": _build_score_breakdown(result),
    }


def _enrich_single_result(result):
    risks = _enrich_risks_with_transparency(result.get("risks", []) or [])
    result["risks"] = risks
    result["grouped_risks"] = _prepare_grouped_risks(risks)
    result["top_issues"] = _prepare_top_issues(risks)
    result["health_summary"] = _build_health_summary(result.get("score", 0), risks)
    result["analysis_context_view"] = _build_analysis_context(result)
    return result


def _enrich_project_result(project_result):
    boards = project_result.get("boards", []) or []
    for board in boards:
        board_risks = _enrich_risks_with_transparency(board.get("risks", []) or [])
        board["risks"] = board_risks
        board["top_issues"] = _prepare_top_issues(board_risks, limit=2)
        board["health_summary"] = _build_health_summary(board.get("score", 0), board_risks)
        board["analysis_context_view"] = _build_analysis_context(board)
    project_result["project_health_summary"] = _build_project_health_summary(project_result)
    return project_result


def _chip_class(severity):
    s = str(severity or "low").lower()
    if s == "critical":
        return "chip-critical"
    if s == "high":
        return "chip-high"
    if s == "medium":
        return "chip-medium"
    return "chip-low"


def _score_band_class(score):
    value = _safe_float(score, 0.0)
    if value >= 8.5:
        return "score-band-excellent"
    if value >= 7.0:
        return "score-band-good"
    if value >= 5.0:
        return "score-band-watch"
    return "score-band-risk"


def _score_band_label(score):
    value = _safe_float(score, 0.0)
    if value >= 8.5:
        return "Strong engineering position"
    if value >= 7.0:
        return "Good with targeted issues"
    if value >= 5.0:
        return "Needs review before release"
    return "High engineering risk"


def _comparison_delta_class(delta, higher_is_better=True):
    if delta == 0:
        return "chip-medium"
    improved = delta > 0 if higher_is_better else delta < 0
    return "chip-low" if improved else "chip-critical"


def _comparison_delta_label(delta, metric_name, higher_is_better=True):
    if delta == 0:
        return f"No change in {metric_name}"
    improved = delta > 0 if higher_is_better else delta < 0
    direction = "improved" if improved else "worsened"
    sign = "+" if delta > 0 else ""
    return f"{metric_name} {direction} ({sign}{delta})"


def _get_recent_runs(limit=None):
    runs = get_recent_runs(RUNS_FOLDER) or []
    if limit is not None:
        return runs[:limit]
    return runs


def _list_run_files(run_name):
    run_dir = os.path.join(RUNS_FOLDER, run_name)
    if not os.path.isdir(run_dir):
        return []
    files = []
    for item in sorted(os.listdir(run_dir)):
        file_path = os.path.join(run_dir, item)
        if os.path.isfile(file_path):
            ext = os.path.splitext(item)[1].lower()
            kind = "other"
            if ext == ".json":
                kind = "json"
            elif ext in {".md", ".txt"}:
                kind = "text"
            elif ext == ".html":
                kind = "html"
            files.append(
                {
                    "run_dir": run_name,
                    "filename": item,
                    "label": item,
                    "kind": kind,
                }
            )
    return files


def _strip_html(text):
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def _safe_preview_text(file_path, limit=1200):
    if not os.path.isfile(file_path):
        return ""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            content = file.read(limit * 3)
    except Exception:
        return ""

    if ext == ".html":
        content = _strip_html(content)

    content = re.sub(r"\s+", " ", content).strip()
    return content[:limit]


def _primary_preview_for_run(run_name):
    run_dir = os.path.join(RUNS_FOLDER, run_name)
    if not os.path.isdir(run_dir):
        return ""

    priority = ["report.md", "report.html", "result.json", ".md", ".txt", ".json", ".html"]
    files = sorted(os.listdir(run_dir))

    for preferred in priority:
        for name in files:
            name_lower = name.lower()
            if preferred.startswith("."):
                matched = name_lower.endswith(preferred)
            else:
                matched = name_lower == preferred
            if matched:
                preview = _safe_preview_text(os.path.join(run_dir, name))
                if preview:
                    return preview

    return ""


def _build_history_runs():
    runs = _get_recent_runs()
    enriched = []

    for run in runs:
        run_name = run.get("name", "")
        files = _list_run_files(run_name)
        preview = _primary_preview_for_run(run_name)
        download_count = len(files)
        html_count = sum(1 for item in files if item["kind"] == "html")
        json_count = sum(1 for item in files if item["kind"] == "json")
        text_count = sum(1 for item in files if item["kind"] == "text")

        enriched.append(
            {
                **run,
                "files": files,
                "preview": preview,
                "download_count": download_count,
                "html_count": html_count,
                "json_count": json_count,
                "text_count": text_count,
                "detail_url": url_for("history_detail_page", run_dir=run_name),
            }
        )

    return enriched


def _build_run_detail(run_name):
    run_dir = os.path.join(RUNS_FOLDER, run_name)
    if not os.path.isdir(run_dir):
        return None

    files = _list_run_files(run_name)
    preview = _primary_preview_for_run(run_name)

    result_json = _safe_json_load(os.path.join(run_dir, "result.json"), {})
    run_record_json = _safe_json_load(os.path.join(run_dir, "run_record.json"), {})
    metadata_json = _safe_json_load(os.path.join(run_dir, "metadata.json"), {})

    merged = {}
    for source in [result_json, run_record_json, metadata_json]:
        if isinstance(source, dict):
            merged.update(source)

    merged.setdefault("name", run_name)
    merged.setdefault("run_dir", run_name)
    merged.setdefault("created_at", merged.get("timestamp", "Unknown"))
    merged.setdefault("run_type", merged.get("analysis_type", "unknown"))

    risks = merged.get("risks", []) or []
    merged["risk_count"] = merged.get("risk_count", len(risks))
    merged["critical_count"] = merged.get(
        "critical_count",
        sum(1 for risk in risks if str(risk.get("severity", "")).lower() == "critical"),
    )
    merged["high_count"] = merged.get(
        "high_count",
        sum(1 for risk in risks if str(risk.get("severity", "")).lower() == "high"),
    )
    merged["medium_count"] = merged.get(
        "medium_count",
        sum(1 for risk in risks if str(risk.get("severity", "")).lower() == "medium"),
    )
    merged["low_count"] = merged.get(
        "low_count",
        sum(1 for risk in risks if str(risk.get("severity", "")).lower() == "low"),
    )

    enriched_result = _enrich_single_result(merged)
    export_summary = _build_export_summary(files, merged)

    return {
        **merged,
        "result": enriched_result,
        "analysis_context_view": enriched_result.get("analysis_context_view", _build_analysis_context(merged)),
        "files": files,
        "preview": preview,
        "download_count": len(files),
        "html_count": sum(1 for item in files if item["kind"] == "html"),
        "json_count": sum(1 for item in files if item["kind"] == "json"),
        "text_count": sum(1 for item in files if item["kind"] == "text"),
        "export_summary": export_summary,
    }


def _build_home_stats():
    all_runs = _get_recent_runs()
    single_count = sum(1 for run in all_runs if run.get("run_type") == "single")
    project_count = sum(1 for run in all_runs if run.get("run_type") == "project")
    return {
        "total_runs": len(all_runs),
        "single_runs": single_count,
        "project_runs": project_count,
        "exported_runs": sum(1 for run in all_runs if _list_run_files(run.get("name", ""))),
    }


def _build_history_summary(history_runs):
    total_files = sum(run["download_count"] for run in history_runs)
    total_html = sum(run["html_count"] for run in history_runs)
    total_json = sum(run["json_count"] for run in history_runs)
    total_text = sum(run["text_count"] for run in history_runs)
    return {
        "total_runs": len(history_runs),
        "total_files": total_files,
        "total_html": total_html,
        "total_json": total_json,
        "total_text": total_text,
    }


def _build_risk_transparency_view(risk):
    metrics = risk.get("metrics") or {}
    explanation = risk.get("explanation") or {}
    fix_suggestion = risk.get("fix_suggestion") or {}

    rule_id = str(risk.get("rule_id") or "rule").lower()
    message = str(risk.get("message") or "No message provided.")
    category = _format_category_name(risk.get("category"))

    threshold = None
    observed = None
    trigger = risk.get("trigger_condition") or "A rule-based design condition triggered this finding."

    if isinstance(metrics, dict):
        if metrics.get("threshold") is not None:
            threshold = metrics.get("threshold")
        if metrics.get("distance") is not None:
            observed = metrics.get("distance")
        elif metrics.get("value") is not None:
            observed = metrics.get("value")

    if rule_id == "spacing":
        trigger = risk.get("trigger_condition") or "Component spacing fell below the configured safe clearance threshold."
    elif rule_id == "thermal":
        trigger = risk.get("trigger_condition") or "Component proximity suggests a local thermal concentration risk."
    elif rule_id == "return_path":
        trigger = risk.get("trigger_condition") or "Signal routing appears to have insufficient return-path support."
    elif rule_id == "impedance":
        trigger = risk.get("trigger_condition") or "Routing geometry suggests impedance control may not stay within target."

    reasoning = explanation.get("root_cause") or f"{category} guidance indicates this condition should be reviewed."
    engineering_impact = explanation.get("impact") or "This issue could affect reliability, manufacturability, or electrical behavior."
    confidence = _extract_risk_confidence_score(risk)

    threshold_text = risk.get("threshold_label")
    observed_label = risk.get("observed_label")

    if observed_label and threshold_text:
        observed_text = f"{observed_label} against {threshold_text}."
    elif observed_label:
        observed_text = observed_label
    elif threshold_text:
        observed_text = threshold_text
    elif threshold is not None and observed is not None:
        observed_text = f"Observed {observed} against a threshold of {threshold}."
    elif observed is not None:
        observed_text = f"Observed value: {observed}."
    elif threshold is not None:
        observed_text = f"Configured threshold: {threshold}."
    else:
        observed_text = "No measured value was preserved for this finding."

    evidence = []
    if risk.get("components"):
        evidence.append(f"Components: {', '.join(risk.get('components', [])[:4])}")
    if risk.get("nets"):
        evidence.append(f"Nets: {', '.join(risk.get('nets', [])[:4])}")
    if fix_suggestion.get("fix"):
        evidence.append(f"Suggested fix: {fix_suggestion.get('fix')}")

    return {
        "trigger": trigger,
        "threshold": threshold,
        "observed_value": observed,
        "observed_text": observed_text,
        "reasoning": reasoning,
        "engineering_impact": engineering_impact,
        "confidence_score": confidence,
        "confidence_band": _confidence_band(confidence),
        "evidence": evidence,
        "message": message,
    }


def _enrich_risks_with_transparency(risks):
    enriched = []
    for risk in risks or []:
        if not isinstance(risk, dict):
            continue
        item = dict(risk)
        item["transparency_view"] = _build_risk_transparency_view(risk)
        enriched.append(item)
    return enriched


def _build_export_summary(files, run_detail):
    files = files or []
    by_kind = defaultdict(int)
    report_files = []

    for file in files:
        kind = file.get("kind") or "other"
        by_kind[kind] += 1
        name = str(file.get("filename") or file.get("label") or "")
        if "report" in name or name.endswith(".html") or name.endswith(".md"):
            report_files.append(file)

    run_name = run_detail.get("name", "Run")
    share_links = []
    for file in report_files[:3]:
        share_links.append(
            {
                "label": file.get("label"),
                "href": _download_href(file),
                "kind": file.get("kind", "other"),
            }
        )

    summary = (
        f"{len(files)} artifact(s) were saved for {run_name}. "
        f"This run can be reopened as structured JSON, readable reports, and downloadable evidence files."
        if files
        else f"No artifacts were saved for {run_name}."
    )

    return {
        "summary": summary,
        "artifact_counts": [
            {"label": key.upper(), "value": value}
            for key, value in sorted(by_kind.items())
        ],
        "share_links": share_links,
        "report_ready": bool(report_files),
    }


def _build_project_timeline_data(project):
    runs = _sort_project_runs(project.get("runs", []))
    if not runs:
        return {
            "events": [],
            "score_chart": _build_series_chart([]),
            "risk_chart": _build_series_chart([]),
            "summary": "No linked runs are available yet for timeline analysis.",
        }

    events = []
    prev_score = None
    prev_risk = None
    for run in runs:
        score_100 = _score_to_100(run.get("score")) if run.get("score") is not None else None
        risk_count = _safe_int(run.get("risk_count"), 0)
        score_delta = round(score_100 - prev_score, 1) if score_100 is not None and prev_score is not None else None
        risk_delta = risk_count - prev_risk if prev_risk is not None else None

        if score_delta is None:
            movement = "Baseline run established."
        elif score_delta > 0 and (risk_delta is None or risk_delta <= 0):
            movement = f"Quality improved by {score_delta} points while risk stayed flat or improved."
        elif score_delta < 0 and (risk_delta is not None and risk_delta > 0):
            movement = f"Risk increased and score dropped by {abs(score_delta)} points."
        else:
            movement = "Run movement was mixed across score and issue volume."

        events.append(
            {
                "name": run.get("name", "Run"),
                "created_at": run.get("created_at", "Unknown"),
                "run_type": run.get("run_type", "unknown"),
                "score": score_100,
                "risk_count": risk_count,
                "critical_count": _safe_int(run.get("critical_count"), 0),
                "score_delta": score_delta,
                "risk_delta": risk_delta,
                "movement": movement,
            }
        )

        if score_100 is not None:
            prev_score = score_100
        prev_risk = risk_count

    score_values = [event["score"] for event in events if event.get("score") is not None]
    score_labels = [event["name"] for event in events if event.get("score") is not None]
    risk_values = [event["risk_count"] for event in events]
    risk_labels = [event["name"] for event in events]

    latest = events[-1]
    summary = (
        f"{len(events)} linked run(s) are now on the project timeline. "
        f"The latest run has {latest.get('risk_count', 0)} finding(s)"
        + (
            f" at a score of {latest.get('score')}."
            if latest.get("score") is not None
            else "."
        )
    )

    return {
        "events": list(reversed(events)),
        "score_chart": _build_series_chart(score_values, score_labels),
        "risk_chart": _build_series_chart(risk_values, risk_labels),
        "summary": summary,
    }


def _build_dashboard_story(recent_runs, projects):
    recent_runs = recent_runs or []
    projects = projects or []

    scored_runs = [run for run in recent_runs if run.get("score") is not None]
    latest_scored = scored_runs[0] if scored_runs else None
    latest_score = _score_to_100(latest_scored.get("score")) if latest_scored else 0

    active_projects = [project for project in projects if project.get("run_count")]
    average_project_score = round(
        sum(_safe_float(project.get("latest_score"), 0.0) for project in active_projects) / len(active_projects),
        1,
    ) if active_projects else 0

    recurring_categories = defaultdict(int)
    for project in projects:
        category = project.get("top_category")
        if category and category != "No recurring category yet":
            recurring_categories[category] += 1

    top_category = None
    if recurring_categories:
        top_category = sorted(recurring_categories.items(), key=lambda item: (-item[1], item[0].lower()))[0][0]

    summary = (
        f"Silicore is currently tracking {len(recent_runs)} saved run(s) and {len(projects)} engineering workspace(s). "
        f"The latest scored run sits at {latest_score} / 100, and active projects average {average_project_score} / 100."
    )
    if top_category:
        summary += f" The most repeated engineering pressure area across workspaces is {top_category}."

    pillars = [
        {
            "title": "Analyze",
            "value": len(recent_runs),
            "copy": "Saved runs are giving the platform a real analysis memory instead of one-off outputs.",
        },
        {
            "title": "Explain",
            "value": latest_score,
            "copy": "The latest score is backed by trend, trust, and decision-support context.",
        },
        {
            "title": "Prioritize",
            "value": len(active_projects),
            "copy": "Active workspaces are now surfacing chronic patterns and what to fix next.",
        },
    ]

    maturity_rows = [
        {
            "title": "Design Analysis Engine",
            "status": "LIVE",
            "status_tone": "low",
            "evidence": f"{len(recent_runs)} saved run(s)",
            "meaning": "Persistent scored analyses, export artifacts, and traceable findings are now available across saved runs.",
        },
        {
            "title": "AI Insight Engine",
            "status": "ACTIVE",
            "status_tone": "low",
            "evidence": top_category or "Growing insight coverage",
            "meaning": "Findings now carry transparency, confidence, clustered patterns, and fix-priority guidance instead of raw issue lists alone.",
        },
        {
            "title": "Project Intelligence",
            "status": "ADVANCING",
            "status_tone": "medium",
            "evidence": f"{len(projects)} workspace(s)",
            "meaning": "Workspace trends, recurring category pressure, board comparison, and timeline summaries are tied to real linked project runs.",
        },
        {
            "title": "Engineering Decision Layer",
            "status": "ACTIVE" if scored_runs else "BOOTSTRAPPING",
            "status_tone": "low" if scored_runs else "medium",
            "evidence": f"{len(active_projects)} active workspace(s)",
            "meaning": "Next-action panels now rank work by severity, confidence, repetition, and board-level impact so engineers know what to fix first.",
        },
    ]

    parser_readiness = []
    for extension, metadata in sorted(FORMAT_READINESS.items()):
        parser_readiness.append(
            {
                "label": metadata.get("label", extension.upper()),
                "status": str(metadata.get("status", "planned")).title(),
                "extension": extension,
            }
        )

    return {
        "summary": summary,
        "pillars": pillars,
        "top_category": top_category or "No recurring category yet",
        "parser_readiness": parser_readiness,
        "maturity_rows": maturity_rows,
    }


def _build_project_comparison(project_result):
    boards = project_result.get("boards", []) or []
    if not boards:
        return {
            "best_board": None,
            "worst_board": None,
            "score_spread": 0.0,
            "strong_count": 0,
            "watch_count": 0,
            "risk_count": 0,
        }

    sorted_boards = sorted(
        boards,
        key=lambda board: _safe_float(board.get("score", 0)),
        reverse=True,
    )
    best_board = sorted_boards[0]
    worst_board = sorted_boards[-1]
    best_score = _safe_float(best_board.get("score", 0))
    worst_score = _safe_float(worst_board.get("score", 0))

    strong_count = sum(1 for board in boards if _safe_float(board.get("score", 0)) >= 8.0)
    watch_count = sum(1 for board in boards if 5.0 <= _safe_float(board.get("score", 0)) < 8.0)
    risk_count = sum(1 for board in boards if _safe_float(board.get("score", 0)) < 5.0)

    return {
        "best_board": best_board,
        "worst_board": worst_board,
        "score_spread": round(best_score - worst_score, 2),
        "strong_count": strong_count,
        "watch_count": watch_count,
        "risk_count": risk_count,
    }


def _project_options():
    projects = list_projects()
    return [
        {
            "project_id": project.get("project_id"),
            "name": project.get("name"),
        }
        for project in projects
    ]


def _build_projects_summary(projects):
    total_projects = len(projects or [])
    total_runs = sum(len(project.get("runs", [])) for project in (projects or []))
    populated_projects = sum(1 for project in (projects or []) if project.get("runs"))
    return {
        "total_projects": total_projects,
        "total_runs": total_runs,
        "populated_projects": populated_projects,
        "empty_projects": max(total_projects - populated_projects, 0),
    }


def _sort_project_runs(runs):
    return sorted(runs or [], key=lambda item: str(item.get("created_at", "")))


def _project_health_label(score_100):
    value = _safe_float(score_100, 0.0)
    if value >= 80:
        return "Strong"
    if value >= 65:
        return "Healthy"
    if value >= 50:
        return "Watch"
    return "At Risk"


def _aggregate_project_categories(runs, limit=5):
    totals = defaultdict(int)

    for run in runs or []:
        summary = run.get("category_summary") or {}
        if isinstance(summary, dict):
            for category, count in summary.items():
                totals[category or "uncategorized"] += _safe_int(count, 0)
            continue

        snapshot = run.get("risk_snapshot") or []
        for item in snapshot:
            if not isinstance(item, dict):
                continue
            category = item.get("category") or "uncategorized"
            totals[category] += 1

    items = [
        {
            "label": _format_category_name(category),
            "value": count,
        }
        for category, count in totals.items()
        if count > 0
    ]
    items.sort(key=lambda item: (-item["value"], item["label"].lower()))
    return items[:limit]


def _enrich_project_for_display(project):
    enriched = dict(project)
    runs = _sort_project_runs(project.get("runs", []))
    enriched["runs"] = runs

    scored_runs = [run for run in runs if run.get("score") is not None]
    score_values = [_score_to_100(run.get("score")) for run in scored_runs]
    risk_values = [_safe_int(run.get("risk_count"), 0) for run in runs]

    latest_run = runs[-1] if runs else None
    latest_scored_run = scored_runs[-1] if scored_runs else None

    latest_score = _score_to_100(latest_scored_run.get("score")) if latest_scored_run else 0
    average_score = round(sum(score_values) / len(score_values), 1) if score_values else 0
    top_categories = _aggregate_project_categories(runs, limit=3)

    enriched["latest_run"] = latest_run
    enriched["latest_score"] = latest_score
    enriched["average_score"] = average_score
    enriched["health_label"] = _project_health_label(latest_score if latest_scored_run else average_score)
    enriched["top_category"] = top_categories[0]["label"] if top_categories else "No recurring category yet"
    enriched["score_trend"] = _build_line_chart(
        score_values,
        [run.get("name", "Run") for run in scored_runs],
        width=240,
        height=72,
        pad_x=12,
        pad_y=10,
    )
    enriched["risk_trend"] = _build_line_chart(
        risk_values,
        [run.get("name", "Run") for run in runs],
        width=240,
        height=72,
        pad_x=12,
        pad_y=10,
    )
    enriched["category_items"] = top_categories

    return enriched


def _normalize_snapshot(snapshot):
    normalized = []

    for item in (snapshot or []):
        if not isinstance(item, dict):
            continue

        risk = dict(item)
        signatures = _build_comparison_signatures(risk)

        risk["message"] = risk.get("message") or "No message provided."
        risk["severity"] = risk.get("severity") or "low"
        risk["category"] = risk.get("category") or "uncategorized"
        risk["recommendation"] = risk.get("recommendation") or "Review this finding."
        risk["components"] = risk.get("components") or []
        risk["nets"] = risk.get("nets") or []
        risk["design_domain"] = risk.get("design_domain") or risk.get("category") or "general"
        risk["base_signature"] = risk.get("base_signature") or signatures["base_signature"]
        risk["signature"] = risk.get("signature") or signatures["signature"]
        risk["normalized_message"] = signatures["normalized_message"]

        normalized.append(risk)

    return normalized


def _normalize_category_summary(summary):
    return summary or {}


def _severity_direction(old_severity, new_severity):
    old_rank = _severity_rank(old_severity)
    new_rank = _severity_rank(new_severity)
    if new_rank < old_rank:
        return "worsened"
    if new_rank > old_rank:
        return "improved"
    return "unchanged"


def _build_delta_analysis(run_a, run_b):
    snapshot_a = _normalize_snapshot(run_a.get("risk_snapshot") or run_a.get("risks"))
    snapshot_b = _normalize_snapshot(run_b.get("risk_snapshot") or run_b.get("risks"))

    sigs_a = {item.get("signature"): item for item in snapshot_a if item.get("signature")}
    sigs_b = {item.get("signature"): item for item in snapshot_b if item.get("signature")}

    base_a = {item.get("base_signature"): item for item in snapshot_a if item.get("base_signature")}
    base_b = {item.get("base_signature"): item for item in snapshot_b if item.get("base_signature")}

    changed_severity = []
    matched_changed_base_signatures = set()

    for base_signature, old_item in base_a.items():
        new_item = base_b.get(base_signature)
        if not new_item:
            continue

        old_severity = str(old_item.get("severity", "")).lower()
        new_severity = str(new_item.get("severity", "")).lower()

        if old_severity != new_severity:
            direction = _severity_direction(old_severity, new_severity)
            changed_severity.append(
                {
                    "base_signature": base_signature,
                    "category": new_item.get("category") or old_item.get("category") or "unknown",
                    "message": new_item.get("message") or old_item.get("message") or "No message provided.",
                    "old_severity": old_severity,
                    "new_severity": new_severity,
                    "direction": direction,
                    "recommendation": new_item.get("recommendation")
                    or old_item.get("recommendation")
                    or "Review this finding.",
                }
            )
            matched_changed_base_signatures.add(base_signature)

    added_risks = []
    for signature, item in sigs_b.items():
        base_signature = item.get("base_signature")
        if base_signature in matched_changed_base_signatures:
            continue
        if signature not in sigs_a:
            added_risks.append(item)

    removed_risks = []
    for signature, item in sigs_a.items():
        base_signature = item.get("base_signature")
        if base_signature in matched_changed_base_signatures:
            continue
        if signature not in sigs_b:
            removed_risks.append(item)

    added_risks = sorted(
        added_risks,
        key=lambda item: (_severity_rank(item.get("severity")), item.get("category", ""), item.get("message", "")),
    )
    removed_risks = sorted(
        removed_risks,
        key=lambda item: (_severity_rank(item.get("severity")), item.get("category", ""), item.get("message", "")),
    )
    changed_severity = sorted(
        changed_severity,
        key=lambda item: (
            _severity_rank(item.get("new_severity")),
            _severity_rank(item.get("old_severity")),
            item.get("category", ""),
            item.get("message", ""),
        ),
    )

    categories_a = _normalize_category_summary(run_a.get("category_summary"))
    categories_b = _normalize_category_summary(run_b.get("category_summary"))

    all_categories = sorted(set(categories_a.keys()) | set(categories_b.keys()))
    category_deltas = []

    for category in all_categories:
        before_count = _safe_int(categories_a.get(category), 0)
        after_count = _safe_int(categories_b.get(category), 0)
        delta = after_count - before_count

        if delta != 0:
            category_deltas.append(
                {
                    "category": category,
                    "before": before_count,
                    "after": after_count,
                    "delta": delta,
                    "direction": "increased" if delta > 0 else "decreased",
                }
            )

    category_deltas = sorted(
        category_deltas,
        key=lambda item: (-abs(item["delta"]), item["category"]),
    )

    domain_totals_a = defaultdict(int)
    domain_totals_b = defaultdict(int)
    for item in snapshot_a:
        domain = str(item.get("design_domain") or item.get("category") or "general").strip().lower()
        domain_totals_a[domain] += 1
    for item in snapshot_b:
        domain = str(item.get("design_domain") or item.get("category") or "general").strip().lower()
        domain_totals_b[domain] += 1

    all_domains = sorted(set(domain_totals_a.keys()) | set(domain_totals_b.keys()))
    domain_deltas = []
    for domain in all_domains:
        before_count = _safe_int(domain_totals_a.get(domain), 0)
        after_count = _safe_int(domain_totals_b.get(domain), 0)
        delta = after_count - before_count
        if delta != 0:
            domain_deltas.append(
                {
                    "domain": domain,
                    "label": _format_category_name(domain),
                    "before": before_count,
                    "after": after_count,
                    "delta": delta,
                    "direction": "increased" if delta > 0 else "decreased",
                }
            )

    domain_deltas = sorted(
        domain_deltas,
        key=lambda item: (-abs(item["delta"]), item["label"].lower()),
    )

    added_critical = [
        risk for risk in added_risks
        if str(risk.get("severity", "")).lower() == "critical"
    ]
    removed_critical = [
        risk for risk in removed_risks
        if str(risk.get("severity", "")).lower() == "critical"
    ]

    severity_improved = [risk for risk in changed_severity if risk.get("direction") == "improved"]
    severity_worsened = [risk for risk in changed_severity if risk.get("direction") == "worsened"]

    insight_lines = []

    if removed_critical:
        insight_lines.append(f"Removed {len(removed_critical)} critical issue(s).")
    if added_critical:
        insight_lines.append(f"Added {len(added_critical)} critical issue(s).")
    if severity_improved:
        insight_lines.append(f"{len(severity_improved)} issue(s) improved in severity.")
    if severity_worsened:
        insight_lines.append(f"{len(severity_worsened)} issue(s) worsened in severity.")
    if removed_risks and not removed_critical:
        insight_lines.append(f"Resolved {len(removed_risks)} prior finding(s).")
    if added_risks and not added_critical:
        insight_lines.append(f"Introduced {len(added_risks)} new finding(s).")

    if category_deltas:
        top_shift = category_deltas[0]
        category_name = _format_category_name(top_shift["category"])
        if top_shift["delta"] > 0:
            insight_lines.append(f"{category_name} issues increased the most.")
        else:
            insight_lines.append(f"{category_name} issues improved the most.")

    if domain_deltas:
        top_domain = domain_deltas[0]
        if top_domain["delta"] > 0:
            insight_lines.append(f"{top_domain['label']} pressure increased across the selected revision window.")
        else:
            insight_lines.append(f"{top_domain['label']} pressure improved across the selected revision window.")

    if not insight_lines:
        insight_lines.append("No finding-level changes were detected between these runs.")

    return {
        "added_risks": added_risks,
        "removed_risks": removed_risks,
        "changed_severity": changed_severity,
        "severity_improved": severity_improved,
        "severity_worsened": severity_worsened,
        "added_count": len(added_risks),
        "removed_count": len(removed_risks),
        "changed_severity_count": len(changed_severity),
        "severity_improved_count": len(severity_improved),
        "severity_worsened_count": len(severity_worsened),
        "added_critical_count": len(added_critical),
        "removed_critical_count": len(removed_critical),
        "category_deltas": category_deltas,
        "domain_deltas": domain_deltas,
        "insight_text": " ".join(insight_lines),
    }


def _score_to_100(score):
    return round(_safe_float(score, 0.0) * 10, 1)


def _build_line_chart(values, labels=None, width=1000, height=180, pad_x=36, pad_y=24):
    values = [_safe_float(value, 0.0) for value in (values or [])]
    labels = labels or []

    if not values:
        return {
            "has_data": False,
            "points": "",
            "area_points": "",
            "width": width,
            "height": height,
            "labels": [],
            "min_value": 0,
            "max_value": 0,
            "last_value": 0,
        }

    min_value = min(values)
    max_value = max(values)
    span = max(max_value - min_value, 1.0)

    def _x(index):
        if len(values) == 1:
            return width / 2
        return pad_x + ((width - (pad_x * 2)) * index / (len(values) - 1))

    def _y(value):
        return height - pad_y - (((value - min_value) / span) * (height - (pad_y * 2)))

    point_pairs = []
    for index, value in enumerate(values):
        point_pairs.append((_x(index), _y(value)))

    points = " ".join(f"{x:.1f},{y:.1f}" for x, y in point_pairs)
    area_points = (
        f"{point_pairs[0][0]:.1f},{height - pad_y:.1f} "
        + points
        + f" {point_pairs[-1][0]:.1f},{height - pad_y:.1f}"
    )

    return {
        "has_data": True,
        "points": points,
        "area_points": area_points,
        "width": width,
        "height": height,
        "labels": labels[: len(values)],
        "min_value": round(min_value, 1),
        "max_value": round(max_value, 1),
        "last_value": round(values[-1], 1),
    }


def _build_bar_chart(items, value_key="value", label_key="label"):
    normalized = []
    max_value = 0.0

    for item in items or []:
        value = _safe_float(item.get(value_key), 0.0)
        max_value = max(max_value, value)
        normalized.append(
            {
                "label": item.get(label_key, ""),
                "value": round(value, 1),
            }
        )

    max_value = max(max_value, 1.0)

    for item in normalized:
        item["width_pct"] = round((item["value"] / max_value) * 100, 1)

    return {
        "has_data": len(normalized) > 0,
        "items": normalized,
        "max_value": round(max_value, 1),
    }


def _build_series_chart(values, labels=None, width=100, height=36):
    chart = _build_line_chart(
        values,
        labels=labels,
        width=width,
        height=height,
        pad_x=4,
        pad_y=4,
    )

    if not chart.get("has_data"):
        return {
            "has_data": False,
            "points": [],
            "guides": [8, 16, 24, 32],
            "width": width,
            "height": height,
            "last_value": 0,
            "delta": 0,
        }

    point_list = []
    for pair in chart.get("points", "").split():
        if "," not in pair:
            continue
        x, y = pair.split(",", 1)
        point_list.append({"x": float(x), "y": float(y)})

    delta = 0
    clean_values = [_safe_float(value, 0.0) for value in (values or [])]
    if len(clean_values) >= 2:
        delta = round(clean_values[-1] - clean_values[0], 1)

    return {
        "has_data": True,
        "points": point_list,
        "guides": [8, 16, 24, 32],
        "width": width,
        "height": height,
        "last_value": chart.get("last_value", 0),
        "delta": delta,
        "min_value": chart.get("min_value", 0),
        "max_value": chart.get("max_value", 0),
    }


def _build_home_chart_data(recent_runs, stats):
    scored_runs = []
    for run in reversed(recent_runs or []):
        score = run.get("score")
        if score is None:
            continue
        scored_runs.append(
            {
                "label": run.get("name", "Run"),
                "value": _score_to_100(score),
            }
        )

    trend = _build_line_chart(
        [item["value"] for item in scored_runs],
        [item["label"] for item in scored_runs],
    )

    latest_score = int(round(scored_runs[-1]["value"])) if scored_runs else 0
    latest_source = scored_runs[-1]["label"] if scored_runs else None

    workflow_chart = _build_bar_chart(
        [
            {"label": "Single", "value": _safe_int(stats.get("single_runs"), 0)},
            {"label": "Project", "value": _safe_int(stats.get("project_runs"), 0)},
            {"label": "Exported", "value": _safe_int(stats.get("exported_runs"), 0)},
        ]
    )

    score_distribution = {"Strong": 0, "Watch": 0, "Risk": 0}
    for item in scored_runs:
        value = _safe_float(item.get("value"), 0.0)
        if value >= 80:
            score_distribution["Strong"] += 1
        elif value >= 50:
            score_distribution["Watch"] += 1
        else:
            score_distribution["Risk"] += 1

    return {
        "trend": trend,
        "latest_score": latest_score,
        "latest_source": latest_source,
        "workflow_chart": workflow_chart,
        "score_distribution": _build_bar_chart(
            [{"label": key, "value": value} for key, value in score_distribution.items() if value > 0]
        ),
        "run_fill_pct": min(round((_safe_int(stats.get("total_runs"), 0) / 20) * 100), 100),
    }


def _build_projects_chart_data(projects):
    projects = projects or []

    portfolio_scores = [
        _safe_float(project.get("latest_score"), 0.0)
        for project in projects
        if project.get("latest_score") is not None
    ]
    portfolio_average_score = round(sum(portfolio_scores) / len(portfolio_scores), 1) if portfolio_scores else 0

    creation_values = []
    creation_labels = []
    running_active = 0
    for project in projects:
        if project.get("run_count", 0) > 0:
            running_active += 1
        creation_values.append(running_active)
        creation_labels.append(project.get("name", "Project"))

    activity_items = [
        {"label": _short_board_label(project.get("name", "Project"), limit=18), "value": project.get("run_count", 0)}
        for project in sorted(projects, key=lambda item: item.get("run_count", 0), reverse=True)[:6]
    ]
    score_items = [
        {
            "label": _short_board_label(project.get("name", "Project"), limit=18),
            "value": project.get("latest_score", 0),
        }
        for project in sorted(projects, key=lambda item: _safe_float(item.get("latest_score"), 0.0), reverse=True)
        if _safe_float(project.get("latest_score"), 0.0) > 0
    ][:6]

    return {
        "portfolio_average_score": portfolio_average_score,
        "activity_bars": _build_bar_chart(activity_items),
        "score_bars": _build_bar_chart(score_items),
        "portfolio_growth": _build_series_chart(creation_values, creation_labels),
    }


def _build_history_chart_data(history_runs):
    score_runs = []
    file_runs = []

    for run in reversed(history_runs or []):
        if run.get("score") is not None:
            score_runs.append(
                {
                    "label": run.get("name", "Run"),
                    "value": _score_to_100(run.get("score")),
                }
            )
        file_runs.append(
            {
                "label": run.get("name", "Run"),
                "value": _safe_int(run.get("download_count"), 0),
            }
        )

    archive_metrics = [
        {
            "label": "Saved Runs",
            "value": len(history_runs or []),
            "note": "Total archived analysis folders",
        },
        {
            "label": "Export Artifacts",
            "value": sum(_safe_int(run.get("download_count"), 0) for run in (history_runs or [])),
            "note": "Files available across archived runs",
        },
        {
            "label": "JSON Outputs",
            "value": sum(_safe_int(run.get("json_count"), 0) for run in (history_runs or [])),
            "note": "Structured outputs for downstream use",
        },
        {
            "label": "HTML Reports",
            "value": sum(_safe_int(run.get("html_count"), 0) for run in (history_runs or [])),
            "note": "Readable report artifacts",
        },
    ]

    return {
        "score_trend": _build_line_chart(
            [item["value"] for item in score_runs],
            [item["label"] for item in score_runs],
        ),
        "artifact_bars": _build_bar_chart(file_runs[:8]),
        "archive_metrics": archive_metrics,
    }


def _project_chart_point_set(values):
    values = [_safe_float(value, 0.0) for value in (values or [])]

    if not values:
        return {"guides": [8, 16, 24, 32], "points": []}

    if len(values) == 1:
        values = [values[0], values[0]]

    min_value = min(values)
    max_value = max(values)
    span = max(max_value - min_value, 1.0)

    points = []
    total = len(values)

    for index, value in enumerate(values):
        x = 0 if total == 1 else round((index / (total - 1)) * 100, 2)
        y = round(32 - (((value - min_value) / span) * 24), 2)
        points.append({"x": x, "y": y, "value": round(value, 1)})

    return {"guides": [8, 16, 24, 32], "points": points}


def _project_tone_from_score(score_value):
    value = _safe_float(score_value, 0.0)
    if value >= 80:
        return "strong"
    if value >= 65:
        return "good"
    if value >= 50:
        return "watch"
    return "risk"


def _short_board_label(name, limit=20):
    name = str(name or "Board")
    if len(name) <= limit:
        return name
    return name[: limit - 3] + "..."


def _build_project_chart_data(project_result, comparison):
    boards = project_result.get("boards", []) or []
    project_summary = project_result.get("project_summary", {}) or {}

    ranking = []
    strong_count = 0
    good_count = 0
    watch_count = 0
    risk_count = 0
    board_score_values = []
    board_labels = []
    board_risk_items = []
    category_totals = defaultdict(int)

    sorted_boards = sorted(
        boards,
        key=lambda board: _safe_float(board.get("score", 0), 0.0),
        reverse=True,
    )

    for board in sorted_boards:
        filename = board.get("filename", "Board")
        score_100 = _score_to_100(board.get("score"))
        tone = _project_tone_from_score(score_100)

        if score_100 >= 80:
            strong_count += 1
        elif score_100 >= 65:
            good_count += 1
        elif score_100 >= 50:
            watch_count += 1
        else:
            risk_count += 1

        board_score_values.append(score_100)
        board_labels.append(_short_board_label(filename))
        board_risk_items.append(
            {
                "label": _short_board_label(filename),
                "value": _safe_int(len(board.get("risks", []) or []), 0),
            }
        )
        ranking.append(
            {
                "label": _short_board_label(filename),
                "value": int(round(score_100)),
                "width": max(0, min(int(round(score_100)), 100)),
                "tone": tone,
            }
        )

        for risk in board.get("risks", []) or []:
            category = risk.get("category") or "uncategorized"
            category_totals[category] += 1

    total_boards = max(len(sorted_boards), 1)
    distribution_bars = []

    if strong_count:
        distribution_bars.append(
            {"label": "Strong", "value": strong_count, "width": round((strong_count / total_boards) * 100, 1), "tone": "strong"}
        )
    if good_count:
        distribution_bars.append(
            {"label": "Good", "value": good_count, "width": round((good_count / total_boards) * 100, 1), "tone": "good"}
        )
    if watch_count:
        distribution_bars.append(
            {"label": "Watch", "value": watch_count, "width": round((watch_count / total_boards) * 100, 1), "tone": "watch"}
        )
    if risk_count:
        distribution_bars.append(
            {"label": "Risk", "value": risk_count, "width": round((risk_count / total_boards) * 100, 1), "tone": "risk"}
        )

    average_score_100 = _score_to_100(project_summary.get("average_score", 0))
    best_score_100 = _score_to_100(project_summary.get("best_score", 0))
    worst_score_100 = _score_to_100(project_summary.get("worst_score", 0))

    hero_trend = _project_chart_point_set(board_score_values)
    score_trend = _project_chart_point_set(board_score_values)
    category_bars = _build_bar_chart(
        [
            {"label": _format_category_name(category), "value": value}
            for category, value in sorted(category_totals.items(), key=lambda item: (-item[1], item[0]))[:5]
        ]
    )

    return {
        "hero_trend": hero_trend,
        "score_trend": score_trend,
        "distribution_bars": distribution_bars,
        "risk_bars": _build_bar_chart(board_risk_items),
        "category_bars": category_bars,
        "ranking": ranking,
        "board_labels": board_labels,
        "summary_points": [
            {"label": "Average", "value": int(round(average_score_100))},
            {"label": "Best", "value": int(round(best_score_100))},
            {"label": "Worst", "value": int(round(worst_score_100))},
        ],
        "comparison": comparison or {},
    }


def _build_project_workspace_chart_data(project):
    runs = _sort_project_runs(project.get("runs", []))
    score_values = [_score_to_100(run.get("score")) for run in runs if run.get("score") is not None]
    score_labels = [run.get("name", "Run") for run in runs if run.get("score") is not None]
    risk_values = [_safe_int(run.get("risk_count"), 0) for run in runs]
    risk_labels = [run.get("name", "Run") for run in runs]
    critical_values = [_safe_int(run.get("critical_count"), 0) for run in runs]

    category_bars = _build_bar_chart(_aggregate_project_categories(runs, limit=5))

    quality_mix = {"Strong": 0, "Healthy": 0, "Watch": 0, "At Risk": 0}
    for run in runs:
        if run.get("score") is None:
            continue
        label = _project_health_label(_score_to_100(run.get("score")))
        quality_mix[label] += 1

    quality_items = [{"label": key, "value": value} for key, value in quality_mix.items() if value > 0]

    latest_two = runs[-2:] if len(runs) >= 2 else runs

    return {
        "score_trend": _build_series_chart(score_values, score_labels),
        "risk_trend": _build_series_chart(risk_values, risk_labels),
        "critical_trend": _build_series_chart(critical_values, risk_labels),
        "category_bars": category_bars,
        "quality_mix": _build_bar_chart(quality_items),
        "latest_compare_run_ids": [run.get("run_id") for run in latest_two if run.get("run_id")],
    }


def _build_compare_visual_data(project_intelligence, insights):
    score_history = project_intelligence.get("score_history", []) if isinstance(project_intelligence, dict) else []
    risk_history = project_intelligence.get("risk_history", []) if isinstance(project_intelligence, dict) else []

    category_items = []
    for item in (insights.get("category_impacts") or [])[:6]:
        delta = _safe_int(item.get("delta"), 0)
        category_items.append(
            {
                "label": item.get("category", "General"),
                "value": abs(delta),
                "tone": "better" if delta < 0 else "worse" if delta > 0 else "flat",
                "signed_delta": delta,
            }
        )

    max_category_value = max([_safe_float(item.get("value"), 0.0) for item in category_items] or [1.0])
    for item in category_items:
        item["width_pct"] = round((_safe_float(item.get("value"), 0.0) / max_category_value) * 100, 1)

    domain_items = []
    for item in (insights.get("domain_impacts") or [])[:6]:
        delta = _safe_int(item.get("delta"), 0)
        domain_items.append(
            {
                "label": item.get("domain", "General"),
                "value": abs(delta),
                "tone": "better" if delta < 0 else "worse" if delta > 0 else "flat",
                "signed_delta": delta,
            }
        )

    max_domain_value = max([_safe_float(item.get("value"), 0.0) for item in domain_items] or [1.0])
    for item in domain_items:
        item["width_pct"] = round((_safe_float(item.get("value"), 0.0) / max_domain_value) * 100, 1)

    return {
        "score_history_chart": _build_series_chart(
            [item.get("value", 0) for item in score_history],
            [item.get("label", "Run") for item in score_history],
        ),
        "risk_history_chart": _build_series_chart(
            [item.get("value", 0) for item in risk_history],
            [item.get("label", "Run") for item in risk_history],
        ),
        "category_shift_bars": category_items,
        "domain_shift_bars": domain_items,
    }


def _build_single_chart_data(result):
    risks = result.get("risks", []) or []
    grouped = result.get("grouped_risks", []) or []
    score_value = _score_to_100(result.get("score"))

    severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for risk in risks:
        severity = str(risk.get("severity", "")).lower()
        if severity == "critical":
            severity_counts["Critical"] += 1
        elif severity == "high":
            severity_counts["High"] += 1
        elif severity == "medium":
            severity_counts["Medium"] += 1
        else:
            severity_counts["Low"] += 1

    category_items = []
    for section in grouped:
        category_items.append(
            {
                "label": section.get("title", "Unknown"),
                "value": _safe_int(section.get("count"), 0),
            }
        )

    penalty_items = []
    score_explanation = result.get("score_explanation") or {}
    for category, penalty in (score_explanation.get("category_totals") or {}).items():
        penalty_items.append(
            {
                "label": str(category).replace("_", " ").title(),
                "value": round(_safe_float(penalty, 0.0) * 10, 1),
            }
        )

    return {
        "score_card": _build_bar_chart(
            [
                {"label": "Board Score", "value": score_value},
                {"label": "Penalty", "value": round(_safe_float(score_explanation.get("total_penalty", 0.0), 0.0) * 10, 1)},
            ]
        ),
        "severity_bars": _build_bar_chart(
            [{"label": key, "value": value} for key, value in severity_counts.items()]
        ),
        "category_bars": _build_bar_chart(category_items),
        "penalty_bars": _build_bar_chart(penalty_items),
    }


def _build_engineering_domain_bars(risks, limit=6):
    domain_totals = defaultdict(int)

    for risk in risks or []:
        domain = str(risk.get("design_domain") or risk.get("category") or "general").strip().lower()
        if not domain:
            domain = "general"
        domain_totals[domain] += 1

    items = [
        {
            "label": _format_category_name(domain),
            "value": count,
        }
        for domain, count in domain_totals.items()
        if count > 0
    ]
    items.sort(key=lambda item: (-item["value"], item["label"].lower()))
    return _build_bar_chart(items[:limit])


def _extract_risk_confidence_score(risk):
    explanation = risk.get("explanation") or {}
    if isinstance(explanation, dict) and explanation.get("confidence") is not None:
        value = _safe_float(explanation.get("confidence"), 0.0)
        if value <= 1.0:
            return round(value * 100, 1)
        return round(value, 1)

    confidence = risk.get("confidence") or {}
    if isinstance(confidence, dict) and confidence.get("score") is not None:
        return round(_safe_float(confidence.get("score"), 0.0), 1)

    score = 42.0
    if risk.get("rule_id"):
        score += 12
    if risk.get("recommendation"):
        score += 10
    if risk.get("metrics"):
        score += 12
    if risk.get("components"):
        score += 10
    if risk.get("nets"):
        score += 8
    if str(risk.get("severity", "")).lower() in {"high", "critical"}:
        score += 6
    return min(round(score, 1), 95.0)


def _confidence_band(score):
    value = _safe_float(score, 0.0)
    if value >= 80:
        return "high"
    if value >= 60:
        return "medium"
    return "low"


def _normalize_pattern_message(message):
    text = _normalize_compare_message(message)
    text = re.sub(r"\b[a-z]+[0-9]+\b", "<ref>", text, flags=re.IGNORECASE)
    text = re.sub(r"\b\d+(?:\.\d+)?\b", "<num>", text)
    text = re.sub(r"\(\s*<num>[^)]*\)", "", text)
    text = " ".join(text.split())
    return text


def _build_single_decision_data(result):
    risks = result.get("risks", []) or []
    if not risks:
        return {
            "average_confidence": 0,
            "confidence_summary": "No finding-level confidence data is available for this board yet.",
            "confidence_bars": _build_bar_chart([]),
            "next_actions": [],
            "trust_note": "No findings were generated, so no next-action ranking is needed.",
        }

    confidence_scores = [_extract_risk_confidence_score(risk) for risk in risks]
    average_confidence = round(sum(confidence_scores) / len(confidence_scores), 1) if confidence_scores else 0

    band_counts = {"High": 0, "Medium": 0, "Low": 0}
    ranked_actions = []

    for risk in risks:
        confidence_score = _extract_risk_confidence_score(risk)
        band = _confidence_band(confidence_score)
        band_counts[band.title()] += 1

        severity_weight = {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(
            str(risk.get("severity", "")).lower(),
            1,
        )
        ranked_actions.append(
            {
                "category": _format_category_name(risk.get("category")),
                "message": risk.get("message", "Unnamed issue"),
                "recommendation": risk.get("recommendation") or "Review this issue in layout.",
                "confidence_score": confidence_score,
                "priority_score": round((severity_weight * 24) + (confidence_score * 0.55), 1),
                "severity": str(risk.get("severity", "low")).lower(),
            }
        )

    ranked_actions.sort(
        key=lambda item: (-item["priority_score"], -item["confidence_score"], item["category"].lower())
    )

    if average_confidence >= 80:
        confidence_summary = "Most current findings have strong support and are credible targets for immediate action."
    elif average_confidence >= 60:
        confidence_summary = "The current board findings are directionally strong, with a few items still needing closer review."
    else:
        confidence_summary = "Several findings have lighter evidence and should be validated before major design decisions."

    top_action = ranked_actions[0] if ranked_actions else None
    trust_note = (
        f"Start with {top_action['category']} because it combines the highest severity and strongest available evidence."
        if top_action
        else "No next action is available."
    )

    focus_items = []
    for item in ranked_actions[:4]:
        focus_items.append(
            {
                "label": item["category"],
                "value": item["priority_score"],
            }
        )

    return {
        "average_confidence": average_confidence,
        "confidence_summary": confidence_summary,
        "confidence_bars": _build_bar_chart(
            [{"label": key, "value": value} for key, value in band_counts.items() if value > 0]
        ),
        "domain_bars": _build_engineering_domain_bars(risks),
        "focus_bars": _build_bar_chart(focus_items),
        "next_actions": ranked_actions[:3],
        "trust_note": trust_note,
    }


def _build_project_review_intelligence(project_result):
    boards = project_result.get("boards", []) or []
    if not boards:
        return {
            "average_confidence": 0,
            "confidence_summary": "No board data is available for project intelligence yet.",
            "board_health_bars": _build_bar_chart([]),
            "chronic_patterns": [],
            "next_actions": [],
            "category_heatmap": [],
        }

    board_health_counts = {"Strong": 0, "Good": 0, "Watch": 0, "Risk": 0}
    pattern_map = defaultdict(lambda: {"count": 0, "boards": set(), "category": "uncategorized", "message": "", "recommendation": "", "severity_weight": 0, "confidence_sum": 0.0})
    category_board_counts = defaultdict(lambda: defaultdict(int))
    action_candidates = []
    confidence_scores = []

    for board in boards:
        score_100 = _score_to_100(board.get("score"))
        if score_100 >= 80:
            board_health_counts["Strong"] += 1
        elif score_100 >= 65:
            board_health_counts["Good"] += 1
        elif score_100 >= 50:
            board_health_counts["Watch"] += 1
        else:
            board_health_counts["Risk"] += 1

        board_name = board.get("filename", "Board")
        board_risks = board.get("risks", []) or []

        for risk in board_risks:
            confidence_score = _extract_risk_confidence_score(risk)
            confidence_scores.append(confidence_score)

            category = risk.get("category") or "uncategorized"
            category_board_counts[category][board_name] += 1

            pattern_key = f"{str(risk.get('rule_id') or 'rule').lower()}|{_normalize_pattern_message(risk.get('message'))}"
            entry = pattern_map[pattern_key]
            entry["count"] += 1
            entry["boards"].add(board_name)
            entry["category"] = category
            entry["message"] = entry["message"] or risk.get("message", "Unnamed issue")
            entry["recommendation"] = entry["recommendation"] or risk.get("recommendation") or "Review this recurring issue."
            severity_weight = {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(str(risk.get("severity", "")).lower(), 1)
            entry["severity_weight"] = max(entry["severity_weight"], severity_weight)
            entry["confidence_sum"] += confidence_score

            action_candidates.append(
                {
                    "board": board_name,
                    "category": _format_category_name(category),
                    "message": risk.get("message", "Unnamed issue"),
                    "recommendation": risk.get("recommendation") or "Review this issue.",
                    "confidence_score": confidence_score,
                    "severity_weight": severity_weight,
                    "priority_score": 0,
                }
            )

    chronic_patterns = []
    for item in pattern_map.values():
        average_confidence = round(item["confidence_sum"] / max(item["count"], 1), 1)
        repeated_boards = len(item["boards"])
        chronic_patterns.append(
            {
                "category": _format_category_name(item["category"]),
                "message": item["message"],
                "recommendation": item["recommendation"],
                "appearances": item["count"],
                "board_count": repeated_boards,
                "average_confidence": average_confidence,
                "priority_score": round((item["severity_weight"] * 32) + (repeated_boards * 18) + (average_confidence * 0.5), 1),
            }
        )

    chronic_patterns.sort(
        key=lambda item: (-item["priority_score"], -item["appearances"], item["category"].lower())
    )

    top_pattern_by_message = {}
    for pattern in chronic_patterns:
        key = (pattern["category"], pattern["message"])
        top_pattern_by_message[key] = pattern["priority_score"]

    for candidate in action_candidates:
        matching_key = (candidate["category"], candidate["message"])
        chronic_bonus = top_pattern_by_message.get(matching_key, 0)
        candidate["priority_score"] = round(
            (candidate["severity_weight"] * 26)
            + (candidate["confidence_score"] * 0.45)
            + (chronic_bonus * 0.4),
            1,
        )

    action_candidates.sort(
        key=lambda item: (-item["priority_score"], -item["confidence_score"], item["board"].lower())
    )

    top_categories = sorted(
        category_board_counts.items(),
        key=lambda item: (-sum(item[1].values()), _format_category_name(item[0]).lower()),
    )[:4]

    category_heatmap = []
    for category, board_counts in top_categories:
        row_cells = []
        max_value = max(board_counts.values()) if board_counts else 1
        for board in boards:
            board_name = board.get("filename", "Board")
            value = board_counts.get(board_name, 0)
            if value >= max_value and value > 0:
                tone = "strong"
            elif value >= 2:
                tone = "medium"
            elif value == 1:
                tone = "light"
            else:
                tone = "none"
            row_cells.append({"board": board_name, "value": value, "tone": tone})
        category_heatmap.append(
            {
                "category": _format_category_name(category),
                "cells": row_cells,
                "total": sum(board_counts.values()),
            }
        )

    average_confidence = round(sum(confidence_scores) / len(confidence_scores), 1) if confidence_scores else 0
    if average_confidence >= 80:
        confidence_summary = "Project findings are strongly supported overall, which makes the current review highly usable for engineering prioritization."
    elif average_confidence >= 60:
        confidence_summary = "Project findings are moderately supported overall and useful for prioritization, with some items still worth validating."
    else:
        confidence_summary = "Project findings are more directional than definitive right now; validate weaker evidence before major decisions."

    return {
        "average_confidence": average_confidence,
        "confidence_summary": confidence_summary,
        "board_health_bars": _build_bar_chart(
            [{"label": key, "value": value} for key, value in board_health_counts.items() if value > 0]
        ),
        "domain_bars": _build_engineering_domain_bars(
            [risk for board in boards for risk in (board.get("risks", []) or [])]
        ),
        "chronic_patterns": chronic_patterns[:5],
        "next_actions": action_candidates[:5],
        "category_heatmap": category_heatmap,
    }


def _build_settings_view_model(editable_config):
    editable_config = editable_config or {}
    sections = {
        "layout": len([key for key, value in (editable_config.get("layout") or {}).items() if value is not None]),
        "power": len([key for key, value in (editable_config.get("power") or {}).items() if value not in [None, []]]),
        "signal": len([key for key, value in (editable_config.get("signal") or {}).items() if value not in [None, []]]),
        "thermal": len([key for key, value in (editable_config.get("thermal") or {}).items() if value is not None]),
        "emi": len([key for key, value in (editable_config.get("emi") or {}).items() if value is not None]),
        "score": len([key for key, value in (editable_config.get("score") or {}).items() if value is not None]),
    }

    penalty_rows = []
    for severity, label in [
        ("penalty_low", "Low"),
        ("penalty_medium", "Medium"),
        ("penalty_high", "High"),
        ("penalty_critical", "Critical"),
    ]:
        penalty_rows.append(
            {
                "label": label,
                "value": _safe_float((editable_config.get("score") or {}).get(severity), 0.0),
            }
        )

    return {
        "section_counts": sections,
        "penalty_bars": _build_bar_chart(penalty_rows),
        "total_controls": sum(sections.values()),
        "advanced_capability_count": 6,
    }


def _download_href(item):
    if isinstance(item, dict):
        if item.get("run_dir") and item.get("filename"):
            return url_for("download_file", run_dir=item["run_dir"], filename=item["filename"])
        if item.get("url"):
            return item["url"]
    return "#"


def _get_nav_items(active_page):
    return [
        {"key": "home", "label": "Dashboard", "subtitle": "Platform overview", "href": url_for("index"), "icon": "◈", "active": active_page == "home"},
        {"key": "single", "label": "Board Analysis", "subtitle": "Single-board review", "href": url_for("single_board_page"), "icon": "▣", "active": active_page == "single"},
        {"key": "project", "label": "Project Review", "subtitle": "Multi-board comparison", "href": url_for("project_page"), "icon": "▤", "active": active_page == "project"},
        {"key": "projects_workspace", "label": "Projects", "subtitle": "Engineering workspaces", "href": url_for("projects_page"), "icon": "◆", "active": active_page == "projects_workspace"},
        {"key": "history", "label": "Saved Runs", "subtitle": "History and outputs", "href": url_for("history_page"), "icon": "◷", "active": active_page == "history"},
        {"key": "settings", "label": "Settings", "subtitle": "Configuration controls", "href": url_for("settings_page"), "icon": "⚙", "active": active_page == "settings"},
    ]


def _render_page(*, active_page, page_title, page_eyebrow, page_copy, template_name, body_context=None):
    body_context = body_context or {}
    return render_template(
        template_name,
        page_title=page_title,
        page_eyebrow=page_eyebrow,
        page_copy=page_copy,
        nav_items=_get_nav_items(active_page),
        chip_class=_chip_class,
        score_band_class=_score_band_class,
        score_band_label=_score_band_label,
        comparison_delta_class=_comparison_delta_class,
        comparison_delta_label=_comparison_delta_label,
        download_href=_download_href,
        **body_context,
    )


def _short_run_label(run, fallback_index):
    label = str(run.get("name") or run.get("run_dir") or f"Run {fallback_index + 1}")
    return label if len(label) <= 24 else label[:21] + "..."


def _build_project_intelligence(project, run_a, run_b):
    runs = project.get("runs", []) or []
    if len(runs) < 2:
        return {
            "trend_summary": "Not enough project history is available to build project-level intelligence yet.",
            "project_takeaway": "Add more linked runs to this project to unlock trend and recurrence analysis.",
            "score_history": [],
            "risk_history": [],
            "recurring_categories": [],
            "recurring_patterns": [],
            "attention_areas": [],
            "stability_label": "Limited history",
            "history_depth": len(runs),
            "selected_window_label": "Current comparison only",
        }

    run_a_id = str(run_a.get("run_id"))
    run_b_id = str(run_b.get("run_id"))

    index_a = next((index for index, run in enumerate(runs) if str(run.get("run_id")) == run_a_id), 0)
    index_b = next((index for index, run in enumerate(runs) if str(run.get("run_id")) == run_b_id), len(runs) - 1)

    start_index = min(index_a, index_b)
    end_index = max(index_a, index_b)

    history_runs = runs[: end_index + 1]
    comparison_window = runs[start_index : end_index + 1]

    score_history = []
    risk_history = []

    for index, run in enumerate(history_runs):
        score_history.append(
            {
                "label": _short_run_label(run, index),
                "value": _score_to_100(run.get("score")),
                "selected": str(run.get("run_id")) in {run_a_id, run_b_id},
                "is_new_run": str(run.get("run_id")) == run_b_id,
            }
        )
        risk_history.append(
            {
                "label": _short_run_label(run, index),
                "value": _safe_int(run.get("risk_count"), 0),
                "selected": str(run.get("run_id")) in {run_a_id, run_b_id},
                "is_new_run": str(run.get("run_id")) == run_b_id,
            }
        )

    category_presence = defaultdict(int)
    category_total_findings = defaultdict(int)
    domain_presence = defaultdict(int)
    domain_total_findings = defaultdict(int)

    pattern_presence = defaultdict(int)
    pattern_examples = {}
    pattern_recommendations = {}

    for run in history_runs:
        category_summary = run.get("category_summary") or {}
        run_seen_categories = set()

        for category, count in category_summary.items():
            normalized_category = category or "uncategorized"
            if normalized_category not in run_seen_categories:
                category_presence[normalized_category] += 1
                run_seen_categories.add(normalized_category)
            category_total_findings[normalized_category] += _safe_int(count, 0)

        snapshot = _normalize_snapshot(run.get("risk_snapshot") or run.get("risks") or [])
        seen_base_signatures = set()
        run_seen_domains = set()

        for item in snapshot:
            domain = str(item.get("design_domain") or item.get("category") or "general").strip().lower()
            if domain not in run_seen_domains:
                domain_presence[domain] += 1
                run_seen_domains.add(domain)
            domain_total_findings[domain] += 1

            base_signature = item.get("base_signature")
            if not base_signature or base_signature in seen_base_signatures:
                continue
            seen_base_signatures.add(base_signature)

            pattern_presence[base_signature] += 1
            pattern_examples.setdefault(
                base_signature,
                {
                    "category": item.get("category") or "uncategorized",
                    "message": item.get("message") or "No message provided.",
                },
            )
            pattern_recommendations.setdefault(
                base_signature,
                item.get("recommendation") or "Review this recurring issue.",
            )

    recurring_categories = []
    for category, appearances in category_presence.items():
        if appearances < 2:
            continue
        recurring_categories.append(
            {
                "category": _format_category_name(category),
                "raw_category": category,
                "appearances": appearances,
                "total_findings": category_total_findings.get(category, 0),
            }
        )

    recurring_categories.sort(
        key=lambda item: (-item["appearances"], -item["total_findings"], item["category"].lower())
    )

    recurring_patterns = []
    for base_signature, appearances in pattern_presence.items():
        if appearances < 2:
            continue
        example = pattern_examples.get(base_signature, {})
        recurring_patterns.append(
            {
                "category": _format_category_name(example.get("category")),
                "message": example.get("message"),
                "appearances": appearances,
                "recommendation": pattern_recommendations.get(base_signature, "Review this recurring issue."),
            }
        )

    recurring_patterns.sort(
        key=lambda item: (-item["appearances"], item["category"].lower(), item["message"].lower())
    )

    recurring_domains = []
    for domain, appearances in domain_presence.items():
        if appearances < 2:
            continue
        recurring_domains.append(
            {
                "domain": _format_category_name(domain),
                "raw_domain": domain,
                "appearances": appearances,
                "total_findings": domain_total_findings.get(domain, 0),
            }
        )

    recurring_domains.sort(
        key=lambda item: (-item["appearances"], -item["total_findings"], item["domain"].lower())
    )

    attention_areas = []
    for item in recurring_categories[:3]:
        attention_areas.append(
            {
                "category": item["category"],
                "reason": (
                    f"{item['category']} appeared in {item['appearances']} project run(s) and contributed "
                    f"{item['total_findings']} total findings across recorded history."
                ),
            }
        )

    first_score = _score_to_100(history_runs[0].get("score"))
    last_score = _score_to_100(history_runs[-1].get("score"))
    selected_start_score = _score_to_100(run_a.get("score"))
    selected_end_score = _score_to_100(run_b.get("score"))

    first_risk = _safe_int(history_runs[0].get("risk_count"), 0)
    last_risk = _safe_int(history_runs[-1].get("risk_count"), 0)
    selected_start_risk = _safe_int(run_a.get("risk_count"), 0)
    selected_end_risk = _safe_int(run_b.get("risk_count"), 0)

    project_score_delta = round(last_score - first_score, 1)
    selected_score_delta = round(selected_end_score - selected_start_score, 1)
    project_risk_delta = last_risk - first_risk
    selected_risk_delta = selected_end_risk - selected_start_risk

    recent_scores = [item["value"] for item in score_history[-3:]]
    if len(recent_scores) >= 3 and recent_scores[-1] >= recent_scores[-2] >= recent_scores[-3]:
        stability_label = "Improving trend"
    elif len(recent_scores) >= 3 and recent_scores[-1] <= recent_scores[-2] <= recent_scores[-3]:
        stability_label = "Weakening trend"
    else:
        stability_label = "Mixed trend"

    if project_score_delta > 0 and project_risk_delta < 0:
        trend_summary = (
            f"Across {len(history_runs)} recorded project run(s), the project score improved by {project_score_delta} points "
            f"while total findings moved by {project_risk_delta}. This suggests the broader project is trending healthier over time."
        )
    elif project_score_delta < 0 and project_risk_delta > 0:
        trend_summary = (
            f"Across {len(history_runs)} recorded project run(s), the project score fell by {abs(project_score_delta)} points "
            f"while total findings increased by {project_risk_delta}. This suggests risk is accumulating across the project."
        )
    else:
        trend_summary = (
            f"Across {len(history_runs)} recorded project run(s), the project trend is mixed. "
            f"Score moved by {project_score_delta} and total findings moved by {project_risk_delta}."
        )

    if recurring_categories:
        top_category = recurring_categories[0]["category"]
        top_domain = recurring_domains[0]["domain"] if recurring_domains else top_category
        project_takeaway = (
            f"The selected comparison improved by {selected_score_delta} points, but {top_category} remains the strongest recurring "
            f"issue family across project history. {top_domain} remains the strongest recurring engineering domain, so the current "
            "revision may be improving while the broader project still shows repeated weakness in the same engineering area."
        )
    else:
        project_takeaway = (
            f"The selected comparison changed by {selected_score_delta} points and no major recurring issue family dominates the "
            "recorded project history yet. This suggests movement is still relatively localized."
        )

    return {
        "trend_summary": trend_summary,
        "project_takeaway": project_takeaway,
        "score_history": score_history,
        "risk_history": risk_history,
        "recurring_categories": recurring_categories[:5],
        "recurring_domains": recurring_domains[:5],
        "recurring_patterns": recurring_patterns[:5],
        "attention_areas": attention_areas,
        "stability_label": stability_label,
        "history_depth": len(history_runs),
        "selected_window_label": f"Runs {start_index + 1} to {end_index + 1}",
        "selected_score_delta": selected_score_delta,
        "selected_risk_delta": selected_risk_delta,
    }


@app.route("/", methods=["GET"])
def index():
    stats = _build_home_stats()
    recent_runs = _get_recent_runs(limit=5)
    projects = [_enrich_project_for_display(project) for project in list_projects()]
    return _render_page(
        active_page="home",
        page_title="Silicore Dashboard",
        page_eyebrow="Hardware Design Intelligence Platform",
        page_copy="Analyze PCB designs, identify engineering risks, compare revisions, and manage project-level design review from a unified control surface.",
        template_name="home.html",
        body_context={
            "stats": stats,
            "recent_runs": recent_runs,
            "home_chart": _build_home_chart_data(recent_runs, stats),
            "dashboard_story": _build_dashboard_story(recent_runs, projects),
            "projects": projects,
        },
    )


@app.route("/single-board", methods=["GET", "POST"])
def single_board_page():
    result = None
    single_chart = None
    single_decision = None

    if request.method == "POST":
        board_file = request.files.get("board_file")
        selected_project_id = (request.form.get("project_id") or "").strip()

        try:
            response = analyze_single_board(
                uploaded_file=board_file,
                upload_folder=UPLOAD_FOLDER,
                runs_folder=RUNS_FOLDER,
                config_path=CONFIG_PATH,
            )

            result = _enrich_single_result(response.get("result") or {})
            single_chart = _build_single_chart_data(result)
            single_decision = _build_single_decision_data(result)

            if selected_project_id:
                add_run_to_project(selected_project_id, response.get("run_record") or {})

            flash("Board analysis completed successfully.")
        except Exception as exc:
            flash(f"Board analysis failed: {exc}")
            return redirect(url_for("single_board_page"))

    return _render_page(
        active_page="single",
        page_title="Board Analysis",
        page_eyebrow="Engineering Review",
        page_copy="Upload a PCB design to generate a focused engineering review, inspect prioritized findings, and export structured analysis outputs.",
        template_name="single_board.html",
        body_context={
            "result": result,
            "project_options": _project_options(),
            "single_chart": single_chart,
            "single_decision": single_decision,
        },
    )


@app.route("/project-review", methods=["GET", "POST"])
def project_page():
    project_result = None
    comparison = None
    project_chart = None
    project_intelligence_review = None

    if request.method == "POST":
        project_files = request.files.getlist("project_files")
        selected_project_id = (request.form.get("project_id") or "").strip()

        try:
            response = analyze_project_files(
                uploaded_files=project_files,
                upload_folder=UPLOAD_FOLDER,
                runs_folder=RUNS_FOLDER,
                config_path=CONFIG_PATH,
            )

            project_result = response.get("project_result", {})
            project_result["project_summary"] = project_result.get("summary", {})
            project_result = _enrich_project_result(project_result)
            comparison = _build_project_comparison(project_result)
            project_chart = _build_project_chart_data(project_result, comparison)
            project_intelligence_review = _build_project_review_intelligence(project_result)

            if selected_project_id:
                add_run_to_project(selected_project_id, response.get("run_record") or {})

            flash("Project analysis completed successfully.")
        except Exception as exc:
            flash(f"Project analysis failed: {exc}")
            return redirect(url_for("project_page"))

    return _render_page(
        active_page="project",
        page_title="Project Review",
        page_eyebrow="Multi-Board Analysis",
        page_copy="Compare multiple boards within a project to evaluate design quality, rank designs, and review overall project health.",
        template_name="project_review.html",
        body_context={
            "project_result": project_result,
            "comparison": comparison,
            "project_options": _project_options(),
            "project_chart": project_chart,
            "project_intelligence_review": project_intelligence_review,
        },
    )


@app.route("/projects", methods=["GET"])
def projects_page():
    projects = [_enrich_project_for_display(project) for project in list_projects()]
    return _render_page(
        active_page="projects_workspace",
        page_title="Projects",
        page_eyebrow="Engineering Workspaces",
        page_copy="Organize boards and saved runs into durable engineering workspaces for cleaner project-level visibility.",
        template_name="projects.html",
        body_context={
            "projects": projects,
            "projects_summary": _build_projects_summary(projects),
            "projects_chart": _build_projects_chart_data(projects),
        },
    )


@app.route("/projects/create", methods=["POST"])
def create_project_route():
    name = (request.form.get("name") or "").strip()
    description = (request.form.get("description") or "").strip()

    if not name:
        flash("Project name is required.")
        return redirect(url_for("projects_page"))

    project = create_project(name, description)
    flash(f"Project '{project['name']}' created successfully.")
    return redirect(url_for("project_detail_page", project_id=project["project_id"]))


@app.route("/projects/<project_id>/delete", methods=["POST"])
def delete_project_route(project_id):
    project = get_project(project_id)

    if not project:
        flash("Project not found.")
        return redirect(url_for("projects_page"))

    project_name = project.get("name", "Project")
    deleted = delete_project(project_id)

    if deleted:
        flash(f"Project '{project_name}' deleted successfully.")
    else:
        flash("Project could not be deleted.")

    return redirect(url_for("projects_page"))


@app.route("/projects/<project_id>", methods=["GET"])
def project_detail_page(project_id):
    project = get_project(project_id)

    if not project:
        flash("Project not found.")
        return redirect(url_for("projects_page"))

    project = _enrich_project_for_display(project)

    return _render_page(
        active_page="projects_workspace",
        page_title=project.get("name", "Project"),
        page_eyebrow="Project Workspace",
        page_copy="Review linked analysis runs, compare revisions, and monitor design progress within this project.",
        template_name="project_detail.html",
        body_context={
            "project": project,
            "workspace_chart": _build_project_workspace_chart_data(project),
            "timeline_data": _build_project_timeline_data(project),
        },
    )


@app.route("/projects/<project_id>/compare", methods=["GET"])
def compare_runs(project_id):
    run_a_id = (request.args.get("run_a") or "").strip()
    run_b_id = (request.args.get("run_b") or "").strip()

    project = get_project(project_id)
    if not project:
        flash("Project not found.")
        return redirect(url_for("projects_page"))

    runs = project.get("runs", []) or []

    if len(runs) < 2:
        flash("At least two runs are required for comparison.")
        return redirect(url_for("project_detail_page", project_id=project_id))
    fallback_run_a = runs[-2]
    fallback_run_b = runs[-1]

    if not run_a_id or not run_b_id:
        run_a = fallback_run_a
        run_b = fallback_run_b
        flash("No compare pair was selected, so Silicore opened the latest two linked runs.")
    elif run_a_id == run_b_id:
        run_a = fallback_run_a
        run_b = fallback_run_b
        flash("The same run was selected twice, so Silicore switched to the latest two different linked runs.")
    else:
        run_a = next((run for run in runs if str(run.get("run_id")) == run_a_id), None)
        run_b = next((run for run in runs if str(run.get("run_id")) == run_b_id), None)

        if not run_a or not run_b:
            run_a = fallback_run_a
            run_b = fallback_run_b
            flash("One or both requested runs could not be found, so Silicore opened the latest valid comparison pair.")

    score_a = _safe_float(run_a.get("score"), 0.0)
    score_b = _safe_float(run_b.get("score"), 0.0)
    risk_a = _safe_int(run_a.get("risk_count"), 0)
    risk_b = _safe_int(run_b.get("risk_count"), 0)
    critical_a = _safe_int(run_a.get("critical_count"), 0)
    critical_b = _safe_int(run_b.get("critical_count"), 0)

    delta_analysis = _build_delta_analysis(run_a, run_b)

    old_risks = run_a.get("risk_snapshot") or run_a.get("risks") or []
    new_risks = run_b.get("risk_snapshot") or run_b.get("risks") or []

    try:
        insights = generate_comparison_insights(
            {
                "old_score": score_a,
                "new_score": score_b,
                "old_risks": old_risks,
                "new_risks": new_risks,
            }
        )
    except Exception as exc:
        print(f"[compare_runs] insight generation failed: {exc}")
        insights = {
            "score_change": {
                "old_score": round(score_a, 2),
                "new_score": round(score_b, 2),
                "delta": round(score_b - score_a, 2),
                "direction": "up" if score_b > score_a else "down" if score_b < score_a else "flat",
                "summary": "Comparison insight generation failed.",
                "engineering_summary": "Comparison insight generation failed, but the base delta comparison is still available.",
            },
            "overview_summary": "Comparison insight generation failed, so only the base delta view may be available.",
            "engineering_takeaway": "Review the raw comparison sections below while the insight layer is unavailable.",
            "stability_state": "changed",
            "risk_diff": {
                "added": [],
                "removed": [],
                "changed": [],
                "unchanged": [],
            },
            "category_impacts": [],
            "top_worsening_categories": [],
            "top_improving_categories": [],
            "recommendations": [],
            "stats": {
                "added_count": 0,
                "removed_count": 0,
                "changed_count": 0,
                "unchanged_count": 0,
                "old_risk_count": len(old_risks),
                "new_risk_count": len(new_risks),
            },
            "confidence_summary": {
                "average_score": 0,
                "band": "low",
                "summary": "No confidence summary is available because insight generation failed.",
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
            },
            "signal_summary": {
                "signal_count": 0,
                "review_count": 0,
                "noise_watch_count": 0,
                "summary": "No signal summary is available because insight generation failed.",
            },
            "trust_summary": {
                "band": "low",
                "summary": "Trust summary unavailable because insight generation failed.",
                "top_focus_confidence": 0,
                "high_confidence_items": 0,
            },
            "trusted_focus_items": [],
            "clustered_added_risks": [],
            "clustered_removed_risks": [],
            "clustered_changed_risks": [],
            "noise_reduction_summary": {
                "raw_total": len(old_risks) + len(new_risks),
                "clustered_total": 0,
                "suppressed_count": 0,
                "reduction_pct": 0,
                "summary": "Noise reduction summary unavailable because insight generation failed.",
            },
        }

    domain_impacts = []
    for item in delta_analysis.get("domain_deltas", []):
        delta = _safe_int(item.get("delta"), 0)
        domain_impacts.append(
            {
                "domain": item.get("label", "General"),
                "delta": delta,
                "direction": "worse" if delta > 0 else "better" if delta < 0 else "flat",
                "summary": f"{item.get('label', 'General')} findings moved from {item.get('before', 0)} to {item.get('after', 0)} across the selected runs.",
                "before": item.get("before", 0),
                "after": item.get("after", 0),
            }
        )

    insights["domain_impacts"] = domain_impacts
    if domain_impacts:
        leading_domain = domain_impacts[0]
        direction_text = "worsened" if leading_domain["delta"] > 0 else "improved"
        insights["engineering_takeaway"] = (
            f"{insights.get('engineering_takeaway', '')} "
            f"The strongest domain-level movement is in {leading_domain['domain']}, which {direction_text} from {leading_domain['before']} to {leading_domain['after']} finding(s)."
        ).strip()

    project_intelligence = _build_project_intelligence(project, run_a, run_b)
    comparison_visuals = _build_compare_visual_data(project_intelligence, insights)

    comparison = {
        "run_a": run_a,
        "run_b": run_b,
        "score_diff": round(score_b - score_a, 2),
        "risk_diff": risk_b - risk_a,
        "critical_diff": critical_b - critical_a,
        "delta_analysis": delta_analysis,
        "insights": insights,
            "project_intelligence": project_intelligence,
            "comparison_visuals": comparison_visuals,
            "summary": {
            "score_changed": round(score_b - score_a, 2),
            "risk_changed": risk_b - risk_a,
            "critical_changed": critical_b - critical_a,
            "score_direction": "improved" if score_b > score_a else "worsened" if score_b < score_a else "unchanged",
            "risk_direction": "improved" if risk_b < risk_a else "worsened" if risk_b > risk_a else "unchanged",
            "critical_direction": "improved" if critical_b < critical_a else "worsened" if critical_b > critical_a else "unchanged",
        },
    }

    return _render_page(
        active_page="projects_workspace",
        page_title="Run Comparison",
        page_eyebrow="Project Comparison",
        page_copy="Compare two linked runs to measure engineering progress, regression, and overall risk movement.",
        template_name="compare.html",
        body_context={
            "project": project,
            "comparison": comparison,
            "comparison_visuals": comparison_visuals,
        },
    )


@app.route("/history", methods=["GET"])
def history_page():
    history_runs = _build_history_runs()
    return _render_page(
        active_page="history",
        page_title="Saved Runs",
        page_eyebrow="Analysis History",
        page_copy="Browse previous analyses, inspect saved outputs, and revisit engineering findings across earlier work.",
        template_name="history.html",
        body_context={
            "history_runs": history_runs,
            "history_summary": _build_history_summary(history_runs),
            "history_chart": _build_history_chart_data(history_runs),
        },
    )


@app.route("/history/<run_dir>", methods=["GET"])
def history_detail_page(run_dir):
    run_detail = _build_run_detail(run_dir)

    if not run_detail:
        flash("Requested run folder was not found.")
        return redirect(url_for("history_page"))

    return _render_page(
        active_page="history",
        page_title="Run Detail",
        page_eyebrow="Saved Run Detail",
        page_copy="Review a saved analysis run in more detail and access every artifact generated for it.",
        template_name="history_detail.html",
        body_context={"run_detail": run_detail},
    )


@app.route("/settings", methods=["GET", "POST"])
def settings_page():
    if request.method == "POST":
        try:
            updated_fields = parse_config_form(request.form)
            save_config(updated_fields, CONFIG_PATH)
            flash("Config saved successfully.")
            return redirect(url_for("settings_page"))
        except Exception as exc:
            flash(f"Config save failed: {exc}")
            return redirect(url_for("settings_page"))

    _, editable_config = get_dashboard_config(CONFIG_PATH)
    settings_view = _build_settings_view_model(editable_config)

    return _render_page(
        active_page="settings",
        page_title="Settings",
        page_eyebrow="Configuration Controls",
        page_copy="Configure analysis thresholds and rule behavior.",
        template_name="settings.html",
        body_context={"editable_config": editable_config, "settings_view": settings_view},
    )


@app.route("/save-config", methods=["POST"])
def save_config_route():
    try:
        updated_fields = parse_config_form(request.form)
        save_config(updated_fields, CONFIG_PATH)
        flash("Config saved successfully.")
    except Exception as exc:
        flash(f"Config save failed: {exc}")

    return redirect(url_for("settings_page"))


@app.route("/download/<run_dir>/<filename>", methods=["GET"])
def download_file(run_dir, filename):
    directory = os.path.join(RUNS_FOLDER, run_dir)
    return send_from_directory(directory, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
