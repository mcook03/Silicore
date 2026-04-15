import json
from uuid import uuid4

from engine.db import get_connection, initialize_database, log_audit_event


def _now(connection):
    return connection.execute("SELECT strftime('%Y-%m-%d %H:%M:%S', 'now') || ' UTC'").fetchone()[0]


def _loads(value, default=None):
    if default is None:
        default = {}
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


def create_job(job_type, payload=None, actor_user_id=None, status="queued"):
    initialize_database()
    connection = get_connection()
    try:
        job_id = str(uuid4())[:12]
        now = _now(connection)
        connection.execute(
            """
            INSERT INTO analysis_jobs (
                job_id, job_type, status, payload_json, result_json, error_text, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (job_id, job_type, status, json.dumps(payload or {}), "{}", None, now, now),
        )
        connection.commit()
    finally:
        connection.close()

    log_audit_event("job.created", actor_user_id=actor_user_id, payload={"job_id": job_id, "job_type": job_type})
    return get_job(job_id)


def update_job(job_id, status=None, result=None, error_text=None):
    initialize_database()
    connection = get_connection()
    try:
        now = _now(connection)
        current = connection.execute(
            "SELECT result_json, error_text, status FROM analysis_jobs WHERE job_id = ?",
            (job_id,),
        ).fetchone()
        if not current:
            return None
        next_status = status or current["status"]
        next_result = json.dumps(result if result is not None else _loads(current["result_json"], {}))
        next_error = error_text if error_text is not None else current["error_text"]
        connection.execute(
            """
            UPDATE analysis_jobs
            SET status = ?, result_json = ?, error_text = ?, updated_at = ?
            WHERE job_id = ?
            """,
            (next_status, next_result, next_error, now, job_id),
        )
        connection.commit()
    finally:
        connection.close()
    return get_job(job_id)


def get_job(job_id):
    initialize_database()
    connection = get_connection()
    try:
        row = connection.execute(
            """
            SELECT job_id, job_type, status, payload_json, result_json, error_text, created_at, updated_at
            FROM analysis_jobs
            WHERE job_id = ?
            """,
            (job_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "job_id": row["job_id"],
            "job_type": row["job_type"],
            "status": row["status"],
            "payload": _loads(row["payload_json"], {}),
            "result": _loads(row["result_json"], {}),
            "error_text": row["error_text"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
    finally:
        connection.close()


def list_jobs(limit=20):
    initialize_database()
    connection = get_connection()
    try:
        rows = connection.execute(
            """
            SELECT job_id, job_type, status, payload_json, result_json, error_text, created_at, updated_at
            FROM analysis_jobs
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (int(limit or 20),),
        ).fetchall()
        return [
            {
                "job_id": row["job_id"],
                "job_type": row["job_type"],
                "status": row["status"],
                "payload": _loads(row["payload_json"], {}),
                "result": _loads(row["result_json"], {}),
                "error_text": row["error_text"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]
    finally:
        connection.close()
