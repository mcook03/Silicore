from uuid import uuid4

from engine.db import get_connection, initialize_database, log_audit_event


def _now_iso(connection):
    return connection.execute("SELECT strftime('%Y-%m-%d %H:%M:%S', 'now') || ' UTC'").fetchone()[0]


def _project_owner(project_row):
    if not project_row or not project_row["owner_user_id"]:
        return None
    return {
        "user_id": project_row["owner_user_id"],
        "name": project_row["owner_name"],
        "email": project_row["owner_email"],
    }


def _project_members(connection, project_id):
    rows = connection.execute(
        """
        SELECT user_id, name, email, member_role, added_at
        FROM project_members
        WHERE project_id = ?
        ORDER BY added_at ASC
        """,
        (project_id,),
    ).fetchall()
    return [
        {
            "user_id": row["user_id"],
            "name": row["name"],
            "email": row["email"],
            "member_role": row["member_role"],
            "added_at": row["added_at"],
        }
        for row in rows
    ]


def _project_notes(connection, project_id):
    rows = connection.execute(
        """
        SELECT note_id, author, body, created_at
        FROM project_notes
        WHERE project_id = ?
        ORDER BY created_at ASC
        """,
        (project_id,),
    ).fetchall()
    return [
        {
            "note_id": row["note_id"],
            "author": row["author"],
            "body": row["body"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def _project_runs(connection, project_id):
    rows = connection.execute(
        """
        SELECT
            r.run_id,
            r.name,
            r.run_type,
            r.created_at,
            r.score,
            r.risk_count,
            r.critical_count,
            r.summary,
            r.path,
            r.metadata_json,
            r.result_json
        FROM project_runs pr
        JOIN runs r ON r.run_id = pr.run_id
        WHERE pr.project_id = ?
        ORDER BY r.created_at ASC
        """,
        (project_id,),
    ).fetchall()
    runs = []
    for row in rows:
        metadata = row["metadata_json"]
        result = row["result_json"]
        run = {
            "run_id": row["run_id"],
            "name": row["name"],
            "run_type": row["run_type"],
            "created_at": row["created_at"],
            "score": row["score"],
            "risk_count": row["risk_count"],
            "critical_count": row["critical_count"],
            "summary": row["summary"],
            "path": row["path"],
            "risk_snapshot": [],
            "category_summary": {},
        }
        try:
            import json

            meta_payload = json.loads(metadata or "{}")
            result_payload = json.loads(result or "{}")
        except Exception:
            meta_payload = {}
            result_payload = {}

        run["risk_snapshot"] = (
            meta_payload.get("risk_snapshot")
            or result_payload.get("risk_snapshot")
            or result_payload.get("risks")
            or []
        )
        if run["score"] is None:
            run["score"] = meta_payload.get("score", result_payload.get("score"))
        if run["risk_count"] in [None, 0] and run["risk_snapshot"]:
            run["risk_count"] = len(run["risk_snapshot"])
        if run["critical_count"] in [None, 0] and run["risk_snapshot"]:
            run["critical_count"] = sum(
                1 for item in run["risk_snapshot"]
                if str((item or {}).get("severity") or "").lower() == "critical"
            )
        run["category_summary"] = (
            meta_payload.get("category_summary")
            or result_payload.get("category_summary")
            or {}
        )
        runs.append(run)
    return runs


def _row_to_project(connection, project_row):
    if not project_row:
        return None
    project_id = project_row["project_id"]
    runs = _project_runs(connection, project_id)
    return {
        "project_id": project_id,
        "name": project_row["name"],
        "description": project_row["description"] or "",
        "created_at": project_row["created_at"],
        "updated_at": project_row["updated_at"],
        "runs": runs,
        "review_status": project_row["review_status"] or "active_review",
        "collaboration_notes": _project_notes(connection, project_id),
        "owner": _project_owner(project_row),
        "team_members": _project_members(connection, project_id),
        "run_count": len(runs),
        "organization_key": project_row["organization_key"] or "personal",
    }


def create_project(name, description="", owner=None):
    initialize_database()
    connection = get_connection()
    try:
        project_id = str(uuid4())[:8]
        now = _now_iso(connection)
        owner_user_id = owner.get("user_id") if isinstance(owner, dict) else None
        owner_name = owner.get("name") if isinstance(owner, dict) else None
        owner_email = owner.get("email") if isinstance(owner, dict) else None
        connection.execute(
            """
            INSERT INTO projects (
                project_id, name, description, review_status, owner_user_id, owner_name,
                owner_email, organization_key, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                (name or "").strip(),
                (description or "").strip(),
                "active_review",
                owner_user_id,
                owner_name,
                owner_email,
                "personal",
                now,
                now,
            ),
        )
        connection.commit()
    finally:
        connection.close()

    log_audit_event(
        "project.created",
        actor_user_id=owner_user_id,
        project_id=project_id,
        payload={"name": (name or "").strip()},
    )
    return get_project(project_id)


def list_projects():
    initialize_database()
    connection = get_connection()
    try:
        rows = connection.execute(
            """
            SELECT *
            FROM projects
            ORDER BY updated_at DESC
            """
        ).fetchall()
        return [_row_to_project(connection, row) for row in rows]
    finally:
        connection.close()


def get_project(project_id):
    initialize_database()
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT * FROM projects WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        return _row_to_project(connection, row)
    finally:
        connection.close()


def delete_project(project_id):
    initialize_database()
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT owner_user_id FROM projects WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        deleted = connection.execute(
            "DELETE FROM projects WHERE project_id = ?",
            (project_id,),
        ).rowcount > 0
        connection.commit()
    finally:
        connection.close()

    if deleted:
        log_audit_event(
            "project.deleted",
            actor_user_id=row["owner_user_id"] if row else None,
            project_id=project_id,
        )
    return deleted


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
    initialize_database()
    normalized_run = _normalize_run(run_record or {})
    if not normalized_run.get("run_id"):
        return None

    connection = get_connection()
    try:
        project_row = connection.execute(
            "SELECT owner_user_id FROM projects WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        if not project_row:
            return None

        now = _now_iso(connection)
        import json

        connection.execute(
            """
            INSERT INTO runs (
                run_id, name, run_type, created_at, path, score, risk_count, critical_count,
                summary, metadata_json, result_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                name = excluded.name,
                run_type = excluded.run_type,
                created_at = excluded.created_at,
                path = excluded.path,
                score = excluded.score,
                risk_count = excluded.risk_count,
                critical_count = excluded.critical_count,
                summary = excluded.summary,
                metadata_json = excluded.metadata_json,
                result_json = excluded.result_json
            """,
            (
                normalized_run["run_id"],
                normalized_run.get("name") or normalized_run["run_id"],
                normalized_run.get("run_type") or "unknown",
                normalized_run.get("created_at") or now,
                normalized_run.get("path"),
                normalized_run.get("score"),
                int(normalized_run.get("risk_count") or 0),
                int(normalized_run.get("critical_count") or 0),
                normalized_run.get("summary"),
                json.dumps(normalized_run),
                json.dumps(
                    {
                        "risk_snapshot": normalized_run.get("risk_snapshot") or [],
                        "category_summary": normalized_run.get("category_summary") or {},
                    }
                ),
            ),
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO project_runs (project_id, run_id, linked_at)
            VALUES (?, ?, ?)
            """,
            (project_id, normalized_run["run_id"], now),
        )
        connection.execute(
            "UPDATE projects SET updated_at = ? WHERE project_id = ?",
            (now, project_id),
        )
        connection.commit()
    finally:
        connection.close()

    log_audit_event(
        "project.run_linked",
        actor_user_id=project_row["owner_user_id"] if project_row else None,
        project_id=project_id,
        run_id=normalized_run["run_id"],
        payload={"run_name": normalized_run.get("name")},
    )
    return get_project(project_id)


def add_project_note(project_id, author, body):
    initialize_database()
    if not (body or "").strip():
        return get_project(project_id)

    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT owner_user_id FROM projects WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        if not row:
            return None
        note_id = str(uuid4())[:10]
        now = _now_iso(connection)
        connection.execute(
            """
            INSERT INTO project_notes (note_id, project_id, author, body, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                note_id,
                project_id,
                (author or "Engineering Review").strip() or "Engineering Review",
                (body or "").strip(),
                now,
            ),
        )
        connection.execute(
            "UPDATE projects SET updated_at = ? WHERE project_id = ?",
            (now, project_id),
        )
        connection.commit()
    finally:
        connection.close()

    log_audit_event(
        "project.note_added",
        actor_user_id=row["owner_user_id"] if row else None,
        project_id=project_id,
        payload={"body": (body or "").strip()},
    )
    return get_project(project_id)


def update_project_review_status(project_id, status):
    initialize_database()
    normalized = (status or "").strip().lower().replace(" ", "_")
    allowed = {
        "active_review",
        "fix_in_progress",
        "re_analysis_planned",
        "ready_for_signoff",
    }
    normalized = normalized if normalized in allowed else "active_review"
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT owner_user_id FROM projects WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        if not row:
            return None
        now = _now_iso(connection)
        connection.execute(
            """
            UPDATE projects
            SET review_status = ?, updated_at = ?
            WHERE project_id = ?
            """,
            (normalized, now, project_id),
        )
        connection.execute(
            """
            INSERT INTO review_decisions (
                decision_id, project_id, status, actor_user_id, created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(uuid4())[:12],
                project_id,
                normalized,
                row["owner_user_id"],
                now,
            ),
        )
        connection.commit()
    finally:
        connection.close()

    log_audit_event(
        "project.review_status_updated",
        actor_user_id=row["owner_user_id"] if row else None,
        project_id=project_id,
        payload={"status": normalized},
    )
    return get_project(project_id)


def create_review_decision(project_id, status, summary="", run_id=None, actor_user_id=None):
    initialize_database()
    normalized = (status or "").strip().lower().replace(" ", "_")
    allowed = {
        "active_review",
        "fix_in_progress",
        "re_analysis_planned",
        "ready_for_signoff",
        "approved",
        "blocked",
    }
    normalized = normalized if normalized in allowed else "active_review"
    summary = (summary or "").strip()

    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT owner_user_id FROM projects WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        if not row:
            return None
        now = _now_iso(connection)
        connection.execute(
            """
            INSERT INTO review_decisions (
                decision_id, project_id, run_id, status, summary, actor_user_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid4())[:12],
                project_id,
                run_id,
                normalized,
                summary or None,
                actor_user_id or row["owner_user_id"],
                now,
            ),
        )
        connection.execute(
            """
            UPDATE projects
            SET review_status = ?, updated_at = ?
            WHERE project_id = ?
            """,
            (normalized if normalized in {
                "active_review",
                "fix_in_progress",
                "re_analysis_planned",
                "ready_for_signoff",
            } else "active_review", now, project_id),
        )
        connection.commit()
    finally:
        connection.close()

    log_audit_event(
        "project.review_decision_created",
        actor_user_id=actor_user_id or (row["owner_user_id"] if row else None),
        project_id=project_id,
        run_id=run_id,
        payload={"status": normalized, "summary": summary},
    )
    return get_project(project_id)


def add_project_member(project_id, user):
    initialize_database()
    if not isinstance(user, dict) or not user.get("user_id"):
        return None

    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT owner_user_id FROM projects WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        if not row:
            return None
        now = _now_iso(connection)
        connection.execute(
            """
            INSERT OR IGNORE INTO project_members (
                project_id, user_id, name, email, member_role, added_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                user.get("user_id"),
                user.get("name"),
                user.get("email"),
                user.get("role") or "member",
                now,
            ),
        )
        connection.execute(
            "UPDATE projects SET updated_at = ? WHERE project_id = ?",
            (now, project_id),
        )
        connection.commit()
    finally:
        connection.close()

    log_audit_event(
        "project.member_added",
        actor_user_id=row["owner_user_id"] if row else None,
        project_id=project_id,
        payload={"member_user_id": user.get("user_id"), "member_email": user.get("email")},
    )
    return get_project(project_id)
