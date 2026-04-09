import json
import os
import re
from collections import defaultdict

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
    risks = result.get("risks", []) or []
    result["grouped_risks"] = _prepare_grouped_risks(risks)
    result["top_issues"] = _prepare_top_issues(risks)
    result["health_summary"] = _build_health_summary(result.get("score", 0), risks)
    result["analysis_context_view"] = _build_analysis_context(result)
    return result


def _enrich_project_result(project_result):
    boards = project_result.get("boards", []) or []
    for board in boards:
        board_risks = board.get("risks", []) or []
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

    return {
        "trend": trend,
        "latest_score": latest_score,
        "latest_source": latest_source,
        "workflow_chart": workflow_chart,
        "run_fill_pct": min(round((_safe_int(stats.get("total_runs"), 0) / 20) * 100), 100),
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
        ranking.append(
            {
                "label": _short_board_label(filename),
                "value": int(round(score_100)),
                "width": max(0, min(int(round(score_100)), 100)),
                "tone": tone,
            }
        )

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

    hero_trend = _project_chart_point_set([worst_score_100, average_score_100, best_score_100])
    score_trend = _project_chart_point_set(board_score_values)

    return {
        "hero_trend": hero_trend,
        "score_trend": score_trend,
        "distribution_bars": distribution_bars,
        "ranking": ranking,
        "comparison": comparison or {},
    }


def _build_single_chart_data(result):
    risks = result.get("risks", []) or []
    grouped = result.get("grouped_risks", []) or []

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
        "severity_bars": _build_bar_chart(
            [{"label": key, "value": value} for key, value in severity_counts.items()]
        ),
        "category_bars": _build_bar_chart(category_items),
        "penalty_bars": _build_bar_chart(penalty_items),
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


@app.route("/", methods=["GET"])
def index():
    stats = _build_home_stats()
    recent_runs = _get_recent_runs(limit=5)
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
        },
    )


@app.route("/single-board", methods=["GET", "POST"])
def single_board_page():
    result = None
    single_chart = None

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
        },
    )


@app.route("/project-review", methods=["GET", "POST"])
def project_page():
    project_result = None
    comparison = None
    project_chart = None

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
        },
    )


@app.route("/projects", methods=["GET"])
def projects_page():
    projects = list_projects()
    return _render_page(
        active_page="projects_workspace",
        page_title="Projects",
        page_eyebrow="Engineering Workspaces",
        page_copy="Organize boards and saved runs into durable engineering workspaces for cleaner project-level visibility.",
        template_name="projects.html",
        body_context={
            "projects": projects,
            "projects_summary": _build_projects_summary(projects),
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

    return _render_page(
        active_page="projects_workspace",
        page_title=project.get("name", "Project"),
        page_eyebrow="Project Workspace",
        page_copy="Review linked analysis runs, compare revisions, and monitor design progress within this project.",
        template_name="project_detail.html",
        body_context={"project": project},
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

    if not run_a_id or not run_b_id:
        flash("Select two runs to compare.")
        return redirect(url_for("project_detail_page", project_id=project_id))

    if run_a_id == run_b_id:
        flash("Choose two different runs for comparison.")
        return redirect(url_for("project_detail_page", project_id=project_id))

    run_a = next((run for run in runs if str(run.get("run_id")) == run_a_id), None)
    run_b = next((run for run in runs if str(run.get("run_id")) == run_b_id), None)

    if not run_a or not run_b:
        flash("One or both selected runs could not be found.")
        return redirect(url_for("project_detail_page", project_id=project_id))

    score_a = _safe_float(run_a.get("score"), 0.0)
    score_b = _safe_float(run_b.get("score"), 0.0)
    risk_a = _safe_int(run_a.get("risk_count"), 0)
    risk_b = _safe_int(run_b.get("risk_count"), 0)
    critical_a = _safe_int(run_a.get("critical_count"), 0)
    critical_b = _safe_int(run_b.get("critical_count"), 0)

    delta_analysis = _build_delta_analysis(run_a, run_b)

    comparison = {
        "run_a": run_a,
        "run_b": run_b,
        "score_diff": round(score_b - score_a, 2),
        "risk_diff": risk_b - risk_a,
        "critical_diff": critical_b - critical_a,
        "delta_analysis": delta_analysis,
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
            current_config, _ = get_dashboard_config(CONFIG_PATH)
            updated_fields = parse_config_form(request.form)
            save_config(CONFIG_PATH, current_config, updated_fields)
            flash("Config saved successfully.")
            return redirect(url_for("settings_page"))
        except Exception as exc:
            flash(f"Config save failed: {exc}")
            return redirect(url_for("settings_page"))

    _, editable_config = get_dashboard_config(CONFIG_PATH)

    return _render_page(
        active_page="settings",
        page_title="Settings",
        page_eyebrow="Configuration Controls",
        page_copy="Configure analysis thresholds and rule behavior.",
        template_name="settings.html",
        body_context={"editable_config": editable_config},
    )


@app.route("/save-config", methods=["POST"])
def save_config_route():
    try:
        current_config, _ = get_dashboard_config(CONFIG_PATH)
        updated_fields = parse_config_form(request.form)
        save_config(CONFIG_PATH, current_config, updated_fields)
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