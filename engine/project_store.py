import json
import os
import uuid
from datetime import datetime, timezone

PROJECTS_FOLDER = "dashboard_projects"


def ensure_projects_folder():
    os.makedirs(PROJECTS_FOLDER, exist_ok=True)


def _project_path(project_id):
    return os.path.join(PROJECTS_FOLDER, f"{project_id}.json")


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def create_project(name, description="", owner=None):
    ensure_projects_folder()
    project_id = str(uuid.uuid4())[:8]

    project = {
        "project_id": project_id,
        "name": (name or "").strip(),
        "description": (description or "").strip(),
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "runs": [],
        "review_status": "active_review",
        "collaboration_notes": [],
        "owner": {
            "user_id": owner.get("user_id"),
            "name": owner.get("name"),
            "email": owner.get("email"),
        } if isinstance(owner, dict) and owner.get("user_id") else None,
        "team_members": [],
    }

    with open(_project_path(project_id), "w", encoding="utf-8") as f:
        json.dump(project, f, indent=2)

    return project


def list_projects():
    ensure_projects_folder()
    projects = []

    for filename in os.listdir(PROJECTS_FOLDER):
        if not filename.endswith(".json"):
            continue

        path = os.path.join(PROJECTS_FOLDER, filename)

        try:
            with open(path, "r", encoding="utf-8") as f:
                project = json.load(f)

            project["run_count"] = len(project.get("runs", []))
            projects.append(project)
        except Exception:
            continue

    projects.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return projects


def get_project(project_id):
    ensure_projects_folder()
    path = _project_path(project_id)

    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_project(project):
    ensure_projects_folder()
    project["updated_at"] = _now_iso()

    with open(_project_path(project["project_id"]), "w", encoding="utf-8") as f:
        json.dump(project, f, indent=2)


def delete_project(project_id):
    ensure_projects_folder()
    path = _project_path(project_id)

    if not os.path.exists(path):
        return False

    os.remove(path)
    return True


def _normalize_run(run_record):
    return {
        "run_id": run_record.get("run_id"),
        "name": run_record.get("name"),
        "run_type": run_record.get("run_type"),
        "created_at": run_record.get("created_at"),
        "score": run_record.get("score"),
        "risk_count": run_record.get("risk_count"),
        "critical_count": run_record.get("critical_count"),
        "summary": run_record.get("summary"),
        "path": run_record.get("path"),
        "risk_snapshot": run_record.get("risk_snapshot", []),
        "category_summary": run_record.get("category_summary", {}),
    }


def add_run_to_project(project_id, run_record):
    project = get_project(project_id)
    if not project:
        return None

    normalized_run = _normalize_run(run_record)

    project.setdefault("runs", [])

    existing_ids = {item.get("run_id") for item in project["runs"]}

    if normalized_run["run_id"] not in existing_ids:
        project["runs"].append(normalized_run)

    save_project(project)
    return project


def add_project_note(project_id, author, body):
    project = get_project(project_id)
    if not project:
        return None

    note = {
        "note_id": str(uuid.uuid4())[:10],
        "author": (author or "Engineering Review").strip() or "Engineering Review",
        "body": (body or "").strip(),
        "created_at": _now_iso(),
    }
    if not note["body"]:
        return project

    project.setdefault("collaboration_notes", [])
    project["collaboration_notes"].append(note)
    save_project(project)
    return project


def update_project_review_status(project_id, status):
    project = get_project(project_id)
    if not project:
        return None

    normalized = (status or "").strip().lower().replace(" ", "_")
    allowed = {
        "active_review",
        "fix_in_progress",
        "re_analysis_planned",
        "ready_for_signoff",
    }
    project["review_status"] = normalized if normalized in allowed else "active_review"
    save_project(project)
    return project


def add_project_member(project_id, user):
    project = get_project(project_id)
    if not project or not isinstance(user, dict) or not user.get("user_id"):
        return None

    project.setdefault("team_members", [])
    existing_ids = {str(item.get("user_id") or "").strip() for item in project["team_members"]}
    if str(user.get("user_id")).strip() not in existing_ids:
        project["team_members"].append(
            {
                "user_id": user.get("user_id"),
                "name": user.get("name"),
                "email": user.get("email"),
            }
        )
    save_project(project)
    return project
