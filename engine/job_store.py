import json
from datetime import datetime, timedelta, timezone
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
                job_id, job_type, status, payload_json, result_json, error_text, claimed_by,
                claimed_at, started_at, completed_at, attempt_count, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (job_id, job_type, status, json.dumps(payload or {}), "{}", None, None, None, None, None, 0, now, now),
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
        completed_at = now if next_status in {"completed", "failed"} else None
        connection.execute(
            """
            UPDATE analysis_jobs
            SET status = ?, result_json = ?, error_text = ?, completed_at = COALESCE(?, completed_at), updated_at = ?
            WHERE job_id = ?
            """,
            (next_status, next_result, next_error, completed_at, now, job_id),
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
                   , claimed_by, claimed_at, started_at, completed_at, attempt_count
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
            "claimed_by": row["claimed_by"],
            "claimed_at": row["claimed_at"],
            "started_at": row["started_at"],
            "completed_at": row["completed_at"],
            "attempt_count": row["attempt_count"] or 0,
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
                   , claimed_by, claimed_at, started_at, completed_at, attempt_count
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
                "claimed_by": row["claimed_by"],
                "claimed_at": row["claimed_at"],
                "started_at": row["started_at"],
                "completed_at": row["completed_at"],
                "attempt_count": row["attempt_count"] or 0,
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]
    finally:
        connection.close()


def claim_jobs(worker_id, limit=10, lease_seconds=90):
    initialize_database()
    connection = get_connection()
    try:
        now_dt = datetime.now(timezone.utc)
        now = _now(connection)
        lease_cutoff = (now_dt - timedelta(seconds=float(lease_seconds or 90))).strftime("%Y-%m-%d %H:%M:%S UTC")
        rows = connection.execute(
            """
            SELECT job_id
            FROM analysis_jobs
            WHERE status = 'queued'
               OR (status = 'running' AND claimed_at IS NOT NULL AND claimed_at < ?)
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (lease_cutoff, int(limit or 10)),
        ).fetchall()
        claimed = []
        for row in rows:
            connection.execute(
                """
                UPDATE analysis_jobs
                SET status = 'running',
                    claimed_by = ?,
                    claimed_at = ?,
                    started_at = COALESCE(started_at, ?),
                    attempt_count = COALESCE(attempt_count, 0) + 1,
                    updated_at = ?
                WHERE job_id = ?
                """,
                (worker_id, now, now, now, row["job_id"]),
            )
            claimed.append(row["job_id"])
        connection.commit()
    finally:
        connection.close()
    return [get_job(job_id) for job_id in claimed]
