import json
import os
from datetime import datetime

from engine.db import get_connection, initialize_database


def ensure_runs_folder(runs_folder="dashboard_runs"):
    os.makedirs(runs_folder, exist_ok=True)
    initialize_database()
    return runs_folder


def create_run_directory(run_type, runs_folder="dashboard_runs"):
    ensure_runs_folder(runs_folder)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_dir_name = f"{run_type}_{timestamp}"
    run_dir_path = os.path.join(runs_folder, run_dir_name)
    os.makedirs(run_dir_path, exist_ok=True)
    return run_dir_name, run_dir_path


def save_run_meta(run_dir_path, meta):
    meta_path = os.path.join(run_dir_path, "run_meta.json")
    with open(meta_path, "w", encoding="utf-8") as file:
        json.dump(meta, file, indent=4)

    initialize_database()
    connection = get_connection()
    try:
        run_id = os.path.basename(run_dir_path)
        connection.execute(
            """
            INSERT INTO runs (
                run_id, name, run_type, created_at, path, filename, score,
                board_count, metadata_json, result_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                name = excluded.name,
                run_type = excluded.run_type,
                created_at = excluded.created_at,
                path = excluded.path,
                filename = excluded.filename,
                score = excluded.score,
                board_count = excluded.board_count,
                metadata_json = excluded.metadata_json
            """,
            (
                run_id,
                meta.get("name") or run_id,
                meta.get("run_type") or "unknown",
                meta.get("created_at") or "",
                run_dir_path,
                meta.get("filename"),
                meta.get("score"),
                meta.get("board_count"),
                json.dumps(meta),
                "{}",
            ),
        )
        connection.commit()
    finally:
        connection.close()


def load_run_meta(run_dir_path):
    meta_path = os.path.join(run_dir_path, "run_meta.json")
    if not os.path.exists(meta_path):
        return {}

    try:
        with open(meta_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return {}


def get_recent_runs(runs_folder="dashboard_runs", limit=10):
    ensure_runs_folder(runs_folder)
    connection = get_connection()
    try:
        rows = connection.execute(
            """
            SELECT run_id, name, path, run_type, created_at
            FROM runs
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (int(limit or 10),),
        ).fetchall()
        if rows:
            return [
                {
                    "name": row["run_id"],
                    "label": row["name"],
                    "path": row["path"],
                    "run_type": row["run_type"],
                    "created_at": row["created_at"],
                }
                for row in rows
            ]
    finally:
        connection.close()

    run_entries = []

    for name in os.listdir(runs_folder):
        run_path = os.path.join(runs_folder, name)

        if not os.path.isdir(run_path):
            continue

        meta = load_run_meta(run_path)

        created_at = meta.get("created_at")
        if not created_at:
            try:
                created_at = datetime.fromtimestamp(os.path.getmtime(run_path)).isoformat()
            except OSError:
                created_at = ""

        run_entries.append(
            {
                "name": name,
                "path": run_path,
                "run_type": meta.get("run_type", "unknown"),
                "created_at": created_at,
            }
        )

    run_entries.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return run_entries[:limit]
