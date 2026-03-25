import json
import os
from datetime import datetime

from engine.report_exporter import export_report_markdown, export_report_html


RUNS_DIR = "dashboard_runs"


def ensure_runs_dir():
    os.makedirs(RUNS_DIR, exist_ok=True)


def make_run_id(prefix):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return f"{prefix}_{timestamp}"


def make_run_dir(run_id):
    ensure_runs_dir()
    run_dir = os.path.join(RUNS_DIR, run_id)
    os.makedirs(run_dir, exist_ok=True)
    return run_dir


def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4)


def save_single_run(single_result):
    run_id = make_run_id("single")
    run_dir = make_run_dir(run_id)

    summary_payload = {
        "run_type": "single",
        "run_id": run_id,
        "board_name": single_result["board_name"],
        "score": single_result["score"],
        "risk_count": single_result["risk_count"],
        "component_count": single_result["component_count"],
        "net_count": single_result["net_count"],
        "report": single_result["report"],
        "risks": single_result["risks"],
    }

    json_path = os.path.join(run_dir, "single_analysis.json")
    md_path = os.path.join(run_dir, "single_report.md")
    html_path = os.path.join(run_dir, "single_report.html")
    meta_path = os.path.join(run_dir, "run_meta.json")

    write_json(json_path, summary_payload)
    export_report_markdown(single_result["report"], md_path)
    export_report_html(single_result["report"], html_path)

    write_json(
        meta_path,
        {
            "run_id": run_id,
            "run_type": "single",
            "title": single_result["board_name"],
            "created_at": datetime.now().isoformat(),
            "files": {
                "json": json_path,
                "md": md_path,
                "html": html_path,
            },
        },
    )

    return {
        "run_id": run_id,
        "run_type": "single",
        "title": single_result["board_name"],
        "json_filename": "single_analysis.json",
        "md_filename": "single_report.md",
        "html_filename": "single_report.html",
    }


def save_project_run(ranked_boards, project_summary, project_report):
    run_id = make_run_id("project")
    run_dir = make_run_dir(run_id)

    summary_payload = {
        "run_type": "project",
        "run_id": run_id,
        "project_summary": project_summary,
        "ranked_boards": ranked_boards,
        "project_report": project_report,
    }

    json_path = os.path.join(run_dir, "project_summary.json")
    md_path = os.path.join(run_dir, "project_summary.md")
    html_path = os.path.join(run_dir, "project_summary.html")
    meta_path = os.path.join(run_dir, "run_meta.json")

    write_json(json_path, summary_payload)
    export_report_markdown(project_report, md_path)
    export_report_html(project_report, html_path)

    write_json(
        meta_path,
        {
            "run_id": run_id,
            "run_type": "project",
            "title": f"{project_summary['boards_analyzed']} board project",
            "created_at": datetime.now().isoformat(),
            "files": {
                "json": json_path,
                "md": md_path,
                "html": html_path,
            },
        },
    )

    return {
        "run_id": run_id,
        "run_type": "project",
        "title": f"{project_summary['boards_analyzed']} board project",
        "json_filename": "project_summary.json",
        "md_filename": "project_summary.md",
        "html_filename": "project_summary.html",
    }


def list_recent_runs(limit=10):
    ensure_runs_dir()

    runs = []
    for run_id in os.listdir(RUNS_DIR):
        run_dir = os.path.join(RUNS_DIR, run_id)
        meta_path = os.path.join(run_dir, "run_meta.json")

        if not os.path.isdir(run_dir):
            continue

        if not os.path.exists(meta_path):
            continue

        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            runs.append(meta)
        except Exception:
            continue

    runs.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return runs[:limit]


def get_download_path(run_id, filename):
    run_dir = os.path.join(RUNS_DIR, run_id)
    file_path = os.path.join(run_dir, filename)

    if not os.path.exists(file_path):
        return None

    return file_path