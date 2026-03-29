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

from engine.config_loader import save_config, parse_config_form
from engine.dashboard_storage import get_recent_runs
from engine.project_store import add_run_to_project, create_project, get_project, list_projects
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


def _severity_rank(severity):
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return order.get(str(severity).lower(), 4)


def _format_category_name(category):
    if not category:
        return "Uncategorized"
    return str(category).replace("_", " ").title()


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
    critical_count = sum(1 for risk in (risks or []) if str(risk.get("severity", "")).lower() == "critical")
    high_count = sum(1 for risk in (risks or []) if str(risk.get("severity", "")).lower() == "high")

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


def _enrich_single_result(result):
    risks = result.get("risks", []) or []
    result["grouped_risks"] = _prepare_grouped_risks(risks)
    result["top_issues"] = _prepare_top_issues(risks)
    result["health_summary"] = _build_health_summary(result.get("score", 0), risks)
    return result


def _enrich_project_result(project_result):
    boards = project_result.get("boards", []) or []
    for board in boards:
        board_risks = board.get("risks", []) or []
        board["top_issues"] = _prepare_top_issues(board_risks, limit=2)
        board["health_summary"] = _build_health_summary(board.get("score", 0), board_risks)
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
            files.append({"run_dir": run_name, "filename": item, "label": item, "kind": kind})
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
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(limit * 3)
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
    priority = [".md", ".txt", ".json", ".html"]
    files = sorted(os.listdir(run_dir))
    for ext in priority:
        for name in files:
            if name.lower().endswith(ext):
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
        html_count = sum(1 for f in files if f["kind"] == "html")
        json_count = sum(1 for f in files if f["kind"] == "json")
        text_count = sum(1 for f in files if f["kind"] == "text")
        enriched.append({
            **run,
            "files": files,
            "preview": preview,
            "download_count": download_count,
            "html_count": html_count,
            "json_count": json_count,
            "text_count": text_count,
            "detail_url": url_for("history_detail_page", run_dir=run_name),
        })
    return enriched


def _build_run_detail(run_name):
    run_dir = os.path.join(RUNS_FOLDER, run_name)
    if not os.path.isdir(run_dir):
        return None
    files = _list_run_files(run_name)
    preview = _primary_preview_for_run(run_name)
    return {
        "name": run_name,
        "files": files,
        "preview": preview,
        "download_count": len(files),
        "html_count": sum(1 for f in files if f["kind"] == "html"),
        "json_count": sum(1 for f in files if f["kind"] == "json"),
        "text_count": sum(1 for f in files if f["kind"] == "text"),
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
    sorted_boards = sorted(boards, key=lambda board: _safe_float(board.get("score", 0)), reverse=True)
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
    return [{"project_id": project.get("project_id"), "name": project.get("name")} for project in projects]


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
    return snapshot or []


def _normalize_category_summary(summary):
    return summary or {}


def _build_delta_analysis(run_a, run_b):
    snapshot_a = _normalize_snapshot(run_a.get("risk_snapshot"))
    snapshot_b = _normalize_snapshot(run_b.get("risk_snapshot"))

    sigs_a = {item.get("signature"): item for item in snapshot_a if item.get("signature")}
    sigs_b = {item.get("signature"): item for item in snapshot_b if item.get("signature")}

    added_keys = [key for key in sigs_b.keys() if key not in sigs_a]
    removed_keys = [key for key in sigs_a.keys() if key not in sigs_b]

    added_risks = [sigs_b[key] for key in added_keys]
    removed_risks = [sigs_a[key] for key in removed_keys]

    added_risks = sorted(
        added_risks,
        key=lambda item: (_severity_rank(item.get("severity")), item.get("category", ""), item.get("message", "")),
    )
    removed_risks = sorted(
        removed_risks,
        key=lambda item: (_severity_rank(item.get("severity")), item.get("category", ""), item.get("message", "")),
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

    added_critical = [risk for risk in added_risks if str(risk.get("severity", "")).lower() == "critical"]
    removed_critical = [risk for risk in removed_risks if str(risk.get("severity", "")).lower() == "critical"]

    insight_lines = []

    if removed_critical:
        insight_lines.append(f"Removed {len(removed_critical)} critical issue(s).")
    if added_critical:
        insight_lines.append(f"Added {len(added_critical)} critical issue(s).")
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
        "added_count": len(added_risks),
        "removed_count": len(removed_risks),
        "added_critical_count": len(added_critical),
        "removed_critical_count": len(removed_critical),
        "category_deltas": category_deltas,
        "insight_text": " ".join(insight_lines),
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
        {"key": "home", "label": "Dashboard", "subtitle": "Control center", "href": url_for("index"), "icon": "◈", "active": active_page == "home"},
        {"key": "single", "label": "Single Board", "subtitle": "Focused review", "href": url_for("single_board_page"), "icon": "▣", "active": active_page == "single"},
        {"key": "project", "label": "Project Review", "subtitle": "Board ranking", "href": url_for("project_page"), "icon": "▤", "active": active_page == "project"},
        {"key": "projects_workspace", "label": "Projects", "subtitle": "Workspace", "href": url_for("projects_page"), "icon": "◆", "active": active_page == "projects_workspace"},
        {"key": "history", "label": "Saved Runs", "subtitle": "History and exports", "href": url_for("history_page"), "icon": "◷", "active": active_page == "history"},
        {"key": "settings", "label": "Settings", "subtitle": "Config editor", "href": url_for("settings_page"), "icon": "⚙", "active": active_page == "settings"},
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
    return _render_page(
        active_page="home",
        page_title="Silicore Dashboard",
        page_eyebrow="Milestone 18 · Structured Product Shell",
        page_copy="A cleaner home page for Silicore that now uses real template files while preserving the premium dark product feel.",
        template_name="home.html",
        body_context={"stats": _build_home_stats(), "recent_runs": _get_recent_runs(limit=5)},
    )


@app.route("/single-board", methods=["GET", "POST"])
def single_board_page():
    result = None
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
            if selected_project_id:
                add_run_to_project(selected_project_id, response.get("run_record") or {})
            flash("Board analysis completed successfully.")
        except Exception as exc:
            flash(f"Board analysis failed: {exc}")
            return redirect(url_for("single_board_page"))

    return _render_page(
        active_page="single",
        page_title="Single Board Analysis",
        page_eyebrow="Board Review",
        page_copy="Upload one board file to generate focused engineering review, clearer issue prioritization, grouped findings, and downloadable exports.",
        template_name="single_board.html",
        body_context={"result": result, "project_options": _project_options()},
    )


@app.route("/project-review", methods=["GET", "POST"])
def project_page():
    project_result = None
    comparison = None
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
            if selected_project_id:
                add_run_to_project(selected_project_id, response.get("run_record") or {})
            flash("Project analysis completed successfully.")
        except Exception as exc:
            flash(f"Project analysis failed: {exc}")
            return redirect(url_for("project_page"))

    return _render_page(
        active_page="project",
        page_title="Project Review",
        page_eyebrow="Project Analysis",
        page_copy="Upload multiple boards to compare design quality, rank boards, and review overall project health in a more product-like comparison flow.",
        template_name="project_review.html",
        body_context={"project_result": project_result, "comparison": comparison, "project_options": _project_options()},
    )


@app.route("/projects", methods=["GET"])
def projects_page():
    projects = list_projects()
    return _render_page(
        active_page="projects_workspace",
        page_title="Projects",
        page_eyebrow="Workspace",
        page_copy="Organize boards and saved runs into durable engineering workspaces.",
        template_name="projects.html",
        body_context={"projects": projects, "projects_summary": _build_projects_summary(projects)},
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
        page_copy="Review all runs linked to this engineering workspace.",
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
        page_copy="Browse previous work, preview saved outputs, and move through run history with a cleaner product-style experience.",
        template_name="history.html",
        body_context={"history_runs": history_runs, "history_summary": _build_history_summary(history_runs)},
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
        page_copy="Review one saved run more closely and access every artifact Silicore generated for it.",
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
        page_eyebrow="Config Editor",
        page_copy="Tune dashboard-facing thresholds in a dedicated settings page while preserving the existing Silicore config save flow.",
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