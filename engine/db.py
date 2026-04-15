import json
import os
import sqlite3
from datetime import datetime, timezone
from urllib.parse import urlparse
from uuid import uuid4

try:
    import psycopg
    from psycopg.rows import dict_row as psycopg_dict_row
except Exception:
    psycopg = None
    psycopg_dict_row = None

try:
    import psycopg2
    import psycopg2.extras
except Exception:
    psycopg2 = None


DB_FOLDER = "dashboard_data"


def _resolve_db_settings():
    database_url = os.environ.get("SILICORE_DATABASE_URL") or os.environ.get("DATABASE_URL")
    db_path = os.environ.get("SILICORE_DB_PATH") or os.path.join(DB_FOLDER, "silicore.db")
    if not database_url:
        return {"engine": "sqlite", "path": db_path, "uri": False}
    if database_url.startswith("sqlite:///"):
        return {"engine": "sqlite", "path": database_url.replace("sqlite:///", "", 1), "uri": False}
    if database_url.startswith("file:"):
        return {"engine": "sqlite", "path": database_url, "uri": True}
    parsed = urlparse(database_url)
    return {"engine": parsed.scheme or "unknown", "path": database_url, "uri": False}


DB_SETTINGS = _resolve_db_settings()
DB_PATH = DB_SETTINGS["path"]


def _driver_available(engine):
    if engine == "sqlite":
        return True
    if engine in {"postgres", "postgresql"}:
        return bool(psycopg or psycopg2)
    return False


def _normalize_sql(sql, engine):
    sql = str(sql or "")
    if engine == "sqlite":
        return sql
    if engine in {"postgres", "postgresql"}:
        stripped = sql.lstrip()
        upper = stripped.upper()
        if upper.startswith("INSERT OR IGNORE INTO "):
            sql = stripped.replace("INSERT OR IGNORE INTO ", "INSERT INTO ", 1)
            sql = f"{sql} ON CONFLICT DO NOTHING"
        result = []
        in_single = False
        in_double = False
        for char in sql:
            if char == "'" and not in_double:
                in_single = not in_single
                result.append(char)
                continue
            if char == '"' and not in_single:
                in_double = not in_double
                result.append(char)
                continue
            if char == "?" and not in_single and not in_double:
                result.append("%s")
            else:
                result.append(char)
        return "".join(result)
    return sql


class DatabaseConnection:
    def __init__(self, engine, connection):
        self.engine = engine
        self._connection = connection

    def execute(self, sql, params=None):
        normalized = _normalize_sql(sql, self.engine)
        if params is None:
            return self._connection.execute(normalized)
        return self._connection.execute(normalized, tuple(params))

    def executescript(self, sql_script):
        if self.engine == "sqlite":
            return self._connection.executescript(sql_script)
        statements = [item.strip() for item in str(sql_script or "").split(";") if item.strip()]
        cursor = None
        for statement in statements:
            cursor = self._connection.execute(statement)
        return cursor

    def commit(self):
        return self._connection.commit()

    def rollback(self):
        return self._connection.rollback()

    def close(self):
        return self._connection.close()

    def __getattr__(self, name):
        return getattr(self._connection, name)


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _now_iso_precise():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f UTC")


def utc_now_text():
    return _now_iso()


def _json_dumps(value):
    if value is None:
        value = {}
    return json.dumps(value, sort_keys=True)


def _json_loads(value, default=None):
    if default is None:
        default = {}
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


def _ensure_db_folder():
    if DB_SETTINGS["engine"] == "sqlite" and not DB_SETTINGS.get("uri"):
        os.makedirs(DB_FOLDER, exist_ok=True)


def get_connection():
    _ensure_db_folder()
    engine = DB_SETTINGS["engine"]
    if engine == "sqlite":
        connection = sqlite3.connect(DB_PATH, uri=bool(DB_SETTINGS.get("uri")))
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return DatabaseConnection(engine, connection)

    if engine in {"postgres", "postgresql"}:
        if psycopg:
            connection = psycopg.connect(DB_SETTINGS["path"], row_factory=psycopg_dict_row)
            return DatabaseConnection(engine, connection)
        if psycopg2:
            connection = psycopg2.connect(DB_SETTINGS["path"], cursor_factory=psycopg2.extras.RealDictCursor)
            return DatabaseConnection(engine, connection)
        raise RuntimeError("PostgreSQL is configured, but no PostgreSQL driver is installed. Install psycopg or psycopg2.")

    raise RuntimeError(f"Unsupported database engine: {engine}")


def database_runtime_info():
    return {
        "engine": DB_SETTINGS["engine"],
        "path": DB_SETTINGS["path"],
        "uri_mode": bool(DB_SETTINGS.get("uri")),
        "driver_available": _driver_available(DB_SETTINGS["engine"]),
    }


def _table_exists(connection, table_name):
    if connection.engine == "sqlite":
        row = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
            (table_name,),
        ).fetchone()
        return row is not None
    row = connection.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _column_exists(connection, table_name, column_name):
    if connection.engine == "sqlite":
        rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        return any(row["name"] == column_name for row in rows)
    rows = connection.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = ? AND column_name = ?
        """,
        (table_name, column_name),
    ).fetchall()
    return bool(rows)


def _ensure_column(connection, table_name, column_name, definition):
    if not _column_exists(connection, table_name, column_name):
        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def initialize_database():
    connection = get_connection()
    try:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS organizations (
                organization_key TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                domain TEXT,
                security_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT,
                role TEXT NOT NULL DEFAULT 'engineer',
                organization_key TEXT NOT NULL DEFAULT 'personal',
                email_verified_at TEXT,
                mfa_enabled INTEGER NOT NULL DEFAULT 0,
                mfa_secret TEXT,
                session_version INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                review_status TEXT NOT NULL DEFAULT 'active_review',
                owner_user_id TEXT,
                owner_name TEXT,
                owner_email TEXT,
                organization_key TEXT NOT NULL DEFAULT 'personal',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(owner_user_id) REFERENCES users(user_id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS project_members (
                project_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                name TEXT,
                email TEXT,
                member_role TEXT NOT NULL DEFAULT 'member',
                added_at TEXT NOT NULL,
                PRIMARY KEY (project_id, user_id),
                FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS project_notes (
                note_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                author TEXT NOT NULL,
                body TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                run_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                path TEXT,
                filename TEXT,
                score REAL,
                risk_count INTEGER NOT NULL DEFAULT 0,
                critical_count INTEGER NOT NULL DEFAULT 0,
                summary TEXT,
                board_count INTEGER,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                result_json TEXT NOT NULL DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS project_runs (
                project_id TEXT NOT NULL,
                run_id TEXT NOT NULL,
                linked_at TEXT NOT NULL,
                PRIMARY KEY (project_id, run_id),
                FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
                FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS atlas_threads (
                thread_id TEXT PRIMARY KEY,
                thread_key TEXT NOT NULL UNIQUE,
                page_type TEXT NOT NULL,
                owner_user_id TEXT,
                project_id TEXT,
                run_id TEXT,
                context_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(owner_user_id) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE SET NULL,
                FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS atlas_messages (
                message_id TEXT PRIMARY KEY,
                thread_id TEXT NOT NULL,
                role TEXT NOT NULL,
                title TEXT,
                copy TEXT NOT NULL,
                detail TEXT,
                intent TEXT,
                citations_json TEXT NOT NULL DEFAULT '[]',
                follow_ups_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                FOREIGN KEY(thread_id) REFERENCES atlas_threads(thread_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS audit_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                actor_user_id TEXT,
                project_id TEXT,
                run_id TEXT,
                thread_id TEXT,
                payload_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY(actor_user_id) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE SET NULL,
                FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE SET NULL,
                FOREIGN KEY(thread_id) REFERENCES atlas_threads(thread_id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS review_decisions (
                decision_id TEXT PRIMARY KEY,
                project_id TEXT,
                run_id TEXT,
                status TEXT NOT NULL,
                summary TEXT,
                actor_user_id TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE SET NULL,
                FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE SET NULL,
                FOREIGN KEY(actor_user_id) REFERENCES users(user_id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS release_gates (
                gate_id TEXT PRIMARY KEY,
                project_id TEXT,
                run_id TEXT,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                required_approvals INTEGER NOT NULL DEFAULT 2,
                approval_count INTEGER NOT NULL DEFAULT 0,
                packet_job_id TEXT,
                target_date TEXT,
                created_by_user_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE SET NULL,
                FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE SET NULL,
                FOREIGN KEY(created_by_user_id) REFERENCES users(user_id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS release_approvals (
                approval_id TEXT PRIMARY KEY,
                gate_id TEXT NOT NULL,
                reviewer_user_id TEXT,
                decision TEXT NOT NULL,
                summary TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(gate_id) REFERENCES release_gates(gate_id) ON DELETE CASCADE,
                FOREIGN KEY(reviewer_user_id) REFERENCES users(user_id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS project_assignments (
                assignment_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT,
                status TEXT NOT NULL DEFAULT 'open',
                priority TEXT NOT NULL DEFAULT 'medium',
                assignee_user_id TEXT,
                assignee_name TEXT,
                assignee_email TEXT,
                due_at TEXT,
                mentions_json TEXT NOT NULL DEFAULT '[]',
                created_by_user_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
                FOREIGN KEY(assignee_user_id) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY(created_by_user_id) REFERENCES users(user_id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS analysis_jobs (
                job_id TEXT PRIMARY KEY,
                job_type TEXT NOT NULL,
                status TEXT NOT NULL,
                payload_json TEXT NOT NULL DEFAULT '{}',
                result_json TEXT NOT NULL DEFAULT '{}',
                error_text TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                token_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                email TEXT NOT NULL,
                token TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS email_verification_tokens (
                token_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                email TEXT NOT NULL,
                token TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS organization_invitations (
                invitation_id TEXT PRIMARY KEY,
                organization_key TEXT NOT NULL,
                email TEXT NOT NULL,
                invited_role TEXT NOT NULL DEFAULT 'engineer',
                token TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'pending',
                invited_by_user_id TEXT,
                accepted_user_id TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                accepted_at TEXT,
                FOREIGN KEY(invited_by_user_id) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY(accepted_user_id) REFERENCES users(user_id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS auth_challenges (
                challenge_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                challenge_type TEXT NOT NULL,
                token TEXT NOT NULL UNIQUE,
                code TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                context_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                consumed_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                session_token TEXT NOT NULL UNIQUE,
                session_version INTEGER NOT NULL DEFAULT 1,
                status TEXT NOT NULL DEFAULT 'active',
                ip_address TEXT,
                user_agent TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS atlas_agent_runs (
                agent_run_id TEXT PRIMARY KEY,
                thread_id TEXT,
                page_type TEXT NOT NULL,
                prompt TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'planned',
                plan_json TEXT NOT NULL DEFAULT '[]',
                results_json TEXT NOT NULL DEFAULT '[]',
                model_mode TEXT NOT NULL DEFAULT 'deterministic',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(thread_id) REFERENCES atlas_threads(thread_id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS evaluation_runs (
                evaluation_id TEXT PRIMARY KEY,
                scope TEXT NOT NULL DEFAULT 'fixtures',
                fixture_count INTEGER NOT NULL DEFAULT 0,
                average_score REAL NOT NULL DEFAULT 0,
                average_parser_confidence REAL NOT NULL DEFAULT 0,
                failed_board_count INTEGER NOT NULL DEFAULT 0,
                summary_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS integration_configs (
                integration_id TEXT PRIMARY KEY,
                integration_type TEXT NOT NULL,
                label TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'configured',
                config_json TEXT NOT NULL DEFAULT '{}',
                created_by_user_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(created_by_user_id) REFERENCES users(user_id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_runs_created_at ON runs(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_projects_updated_at ON projects(updated_at DESC);
            CREATE INDEX IF NOT EXISTS idx_atlas_messages_thread_time ON atlas_messages(thread_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_audit_events_time ON audit_events(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_user_sessions_user_time ON user_sessions(user_id, created_at DESC);
            """
        )
        _ensure_schema_migrations(connection)
        _migrate_legacy_data(connection)
        connection.commit()
    finally:
        connection.close()


def _ensure_schema_migrations(connection):
    _ensure_column(connection, "organizations", "domain", "TEXT")
    _ensure_column(connection, "organizations", "security_json", "TEXT NOT NULL DEFAULT '{}'")
    _ensure_column(connection, "users", "email_verified_at", "TEXT")
    _ensure_column(connection, "users", "mfa_enabled", "INTEGER NOT NULL DEFAULT 0")
    _ensure_column(connection, "users", "mfa_secret", "TEXT")
    _ensure_column(connection, "users", "session_version", "INTEGER NOT NULL DEFAULT 1")
    _ensure_column(connection, "analysis_jobs", "claimed_by", "TEXT")
    _ensure_column(connection, "analysis_jobs", "claimed_at", "TEXT")
    _ensure_column(connection, "analysis_jobs", "started_at", "TEXT")
    _ensure_column(connection, "analysis_jobs", "completed_at", "TEXT")
    _ensure_column(connection, "analysis_jobs", "attempt_count", "INTEGER NOT NULL DEFAULT 0")


def _get_state(connection, key):
    row = connection.execute("SELECT value FROM app_state WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def _set_state(connection, key, value):
    connection.execute(
        """
        INSERT INTO app_state (key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            updated_at = excluded.updated_at
        """,
        (key, value, _now_iso()),
    )


def _migrate_legacy_data(connection):
    if _get_state(connection, "legacy_migration_v1") == "complete":
        return

    _migrate_legacy_users(connection)
    _migrate_legacy_runs(connection)
    _migrate_legacy_projects(connection)
    _set_state(connection, "legacy_migration_v1", "complete")


def _safe_json_file(path, default=None):
    if default is None:
        default = {}
    if not os.path.isfile(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return default


def _migrate_legacy_users(connection):
    users_path = os.path.join("dashboard_users", "users.json")
    payload = _safe_json_file(users_path, {"users": []})
    connection.execute(
        """
        INSERT OR IGNORE INTO organizations (organization_key, name, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        ("personal", "Personal Workspace", _now_iso(), _now_iso()),
    )
    for user in payload.get("users", []) or []:
        email = str(user.get("email") or "").strip().lower()
        if not email:
            continue
        connection.execute(
            """
            INSERT OR IGNORE INTO users (
                user_id, name, email, password_hash, role, organization_key, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user.get("user_id") or str(uuid4())[:10],
                user.get("name") or "Engineer",
                email,
                user.get("password_hash"),
                user.get("role") or "engineer",
                user.get("organization_key") or "personal",
                user.get("created_at") or _now_iso(),
                user.get("created_at") or _now_iso(),
            ),
        )


def _migrate_legacy_runs(connection):
    runs_folder = "dashboard_runs"
    if not os.path.isdir(runs_folder):
        return

    for entry in sorted(os.listdir(runs_folder)):
        run_path = os.path.join(runs_folder, entry)
        if not os.path.isdir(run_path):
            continue

        meta = _safe_json_file(os.path.join(run_path, "run_meta.json"), {})
        result = (
            _safe_json_file(os.path.join(run_path, "single_analysis.json"), {})
            or _safe_json_file(os.path.join(run_path, "project_summary.json"), {})
            or _safe_json_file(os.path.join(run_path, "result.json"), {})
        )

        score = result.get("score", meta.get("score"))
        risk_count = result.get("risk_count")
        if risk_count is None and isinstance(result.get("risks"), list):
            risk_count = len(result.get("risks") or [])
        critical_count = result.get("critical_count")
        if critical_count is None and isinstance(result.get("risks"), list):
            critical_count = sum(
                1 for risk in (result.get("risks") or [])
                if str((risk or {}).get("severity") or "").lower() == "critical"
            )

        connection.execute(
            """
            INSERT OR IGNORE INTO runs (
                run_id, name, run_type, created_at, path, filename, score, risk_count,
                critical_count, summary, board_count, metadata_json, result_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry,
                meta.get("name") or entry,
                meta.get("run_type") or "unknown",
                meta.get("created_at") or result.get("generated_at") or _now_iso(),
                run_path,
                meta.get("filename"),
                score,
                int(risk_count or 0),
                int(critical_count or 0),
                ((result.get("executive_summary") or {}).get("summary") if isinstance(result, dict) else None),
                meta.get("board_count"),
                _json_dumps(meta),
                _json_dumps(result),
            ),
        )


def _migrate_legacy_projects(connection):
    projects_folder = "dashboard_projects"
    if not os.path.isdir(projects_folder):
        return

    for entry in sorted(os.listdir(projects_folder)):
        if not entry.endswith(".json"):
            continue

        project = _safe_json_file(os.path.join(projects_folder, entry), {})
        project_id = project.get("project_id") or os.path.splitext(entry)[0]
        owner = project.get("owner") or {}

        connection.execute(
            """
            INSERT OR IGNORE INTO projects (
                project_id, name, description, review_status, owner_user_id, owner_name,
                owner_email, organization_key, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                project.get("name") or project_id,
                project.get("description") or "",
                project.get("review_status") or "active_review",
                owner.get("user_id"),
                owner.get("name"),
                owner.get("email"),
                project.get("organization_key") or "personal",
                project.get("created_at") or _now_iso(),
                project.get("updated_at") or project.get("created_at") or _now_iso(),
            ),
        )

        for member in project.get("team_members", []) or []:
            connection.execute(
                """
                INSERT OR IGNORE INTO project_members (
                    project_id, user_id, name, email, member_role, added_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    member.get("user_id") or str(uuid4())[:10],
                    member.get("name"),
                    member.get("email"),
                    member.get("member_role") or "member",
                    member.get("added_at") or _now_iso(),
                ),
            )

        for note in project.get("collaboration_notes", []) or []:
            connection.execute(
                """
                INSERT OR IGNORE INTO project_notes (
                    note_id, project_id, author, body, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    note.get("note_id") or str(uuid4())[:10],
                    project_id,
                    note.get("author") or "Engineering Review",
                    note.get("body") or "",
                    note.get("created_at") or _now_iso(),
                ),
            )

        for run in project.get("runs", []) or []:
            run_id = run.get("run_id") or str(uuid4())[:12]
            connection.execute(
                """
                INSERT OR IGNORE INTO runs (
                    run_id, name, run_type, created_at, path, score, risk_count, critical_count,
                    summary, metadata_json, result_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    run.get("name") or run_id,
                    run.get("run_type") or "unknown",
                    run.get("created_at") or _now_iso(),
                    run.get("path"),
                    run.get("score"),
                    int(run.get("risk_count") or 0),
                    int(run.get("critical_count") or 0),
                    run.get("summary"),
                    _json_dumps(run),
                    _json_dumps(
                        {
                            "risk_snapshot": run.get("risk_snapshot") or [],
                            "category_summary": run.get("category_summary") or {},
                        }
                    ),
                ),
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO project_runs (project_id, run_id, linked_at)
                VALUES (?, ?, ?)
                """,
                (project_id, run_id, _now_iso()),
            )


def log_audit_event(event_type, actor_user_id=None, project_id=None, run_id=None, thread_id=None, payload=None):
    initialize_database()
    connection = get_connection()
    try:
        connection.execute(
            """
            INSERT INTO audit_events (
                event_id, event_type, actor_user_id, project_id, run_id, thread_id, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid4())[:12],
                event_type,
                actor_user_id,
                project_id,
                run_id,
                thread_id,
                _json_dumps(payload),
                _now_iso(),
            ),
        )
        connection.commit()
    finally:
        connection.close()


def _assistant_copy(answer, detail=None):
    answer = str(answer or "").strip()
    detail = str(detail or "").strip()
    if "<" in answer and ">" in answer:
        return f"{answer}<p class=\"assistant-detail-copy\">{detail}</p>" if detail else answer
    copy = f"<p>{answer}</p>" if answer else "<p>No answer available yet.</p>"
    if detail:
        copy += f"<p class=\"assistant-detail-copy\">{detail}</p>"
    return copy


def _project_and_run_from_context(context):
    if not isinstance(context, dict):
        return None, None
    project_id = context.get("project_id")
    run_id = context.get("run_id") or context.get("run_dir")
    return project_id, run_id


def _existing_id(connection, table_name, key_name, value):
    if not value:
        return None
    row = connection.execute(
        f"SELECT {key_name} FROM {table_name} WHERE {key_name} = ?",
        (value,),
    ).fetchone()
    return row[key_name] if row else None


def persist_atlas_exchange(thread_key, page_type, context, prompt, answer_payload, owner_user_id=None):
    initialize_database()
    connection = get_connection()
    try:
        thread_now = _now_iso()
        user_created_at = _now_iso_precise()
        assistant_created_at = _now_iso_precise()
        project_id, run_id = _project_and_run_from_context(context)
        project_id = _existing_id(connection, "projects", "project_id", project_id)
        run_id = _existing_id(connection, "runs", "run_id", run_id)
        thread = connection.execute(
            "SELECT thread_id FROM atlas_threads WHERE thread_key = ?",
            (thread_key,),
        ).fetchone()
        if thread:
            thread_id = thread["thread_id"]
            connection.execute(
                """
                UPDATE atlas_threads
                SET page_type = ?, owner_user_id = COALESCE(?, owner_user_id),
                    project_id = COALESCE(?, project_id), run_id = COALESCE(?, run_id),
                    context_json = ?, updated_at = ?
                WHERE thread_id = ?
                """,
                (
                    page_type,
                    owner_user_id,
                    project_id,
                    run_id,
                    _json_dumps(context),
                    thread_now,
                    thread_id,
                ),
            )
        else:
            thread_id = str(uuid4())[:12]
            connection.execute(
                """
                INSERT INTO atlas_threads (
                    thread_id, thread_key, page_type, owner_user_id, project_id, run_id,
                    context_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    thread_id,
                    thread_key,
                    page_type,
                    owner_user_id,
                    project_id,
                    run_id,
                    _json_dumps(context),
                    thread_now,
                    thread_now,
                ),
            )

        connection.execute(
            """
            INSERT INTO atlas_messages (
                message_id, thread_id, role, title, copy, detail, intent,
                citations_json, follow_ups_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid4())[:12],
                thread_id,
                "user",
                None,
                str(prompt or "").strip(),
                None,
                None,
                "[]",
                "[]",
                user_created_at,
            ),
        )

        answer = answer_payload or {}
        connection.execute(
            """
            INSERT INTO atlas_messages (
                message_id, thread_id, role, title, copy, detail, intent,
                citations_json, follow_ups_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid4())[:12],
                thread_id,
                "assistant",
                answer.get("title"),
                _assistant_copy(answer.get("answer"), answer.get("detail")),
                answer.get("detail"),
                answer.get("intent"),
                _json_dumps(answer.get("citations") or []),
                _json_dumps(answer.get("follow_ups") or []),
                assistant_created_at,
            ),
        )

        connection.commit()
        log_audit_event(
            "atlas.query",
            actor_user_id=owner_user_id,
            project_id=project_id,
            run_id=run_id,
            thread_id=thread_id,
            payload={
                "page_type": page_type,
                "thread_key": thread_key,
                "prompt": prompt,
                "intent": answer.get("intent"),
            },
        )
        return list_atlas_messages(thread_key)
    finally:
        connection.close()


def list_atlas_messages(thread_key):
    initialize_database()
    connection = get_connection()
    try:
        thread = connection.execute(
            "SELECT thread_id FROM atlas_threads WHERE thread_key = ?",
            (thread_key,),
        ).fetchone()
        if not thread:
            return []

        rows = connection.execute(
            """
            SELECT message_id, role, title, copy, detail, intent, citations_json, follow_ups_json, created_at
            FROM atlas_messages
            WHERE thread_id = ?
            ORDER BY created_at ASC, message_id ASC
            """,
            (thread["thread_id"],),
        ).fetchall()

        return [
            {
                "role": row["role"],
                "title": row["title"],
                "copy": row["copy"],
                "detail": row["detail"],
                "intent": row["intent"] or "",
                "citations": _json_loads(row["citations_json"], []),
                "follow_ups": _json_loads(row["follow_ups_json"], []),
                "created_at": row["created_at"],
            }
            for row in rows
        ]
    finally:
        connection.close()


def persist_atlas_agent_run(thread_key, page_type, prompt, plan, results, model_mode="deterministic", status="completed"):
    initialize_database()
    connection = get_connection()
    try:
        now = _now_iso()
        thread = connection.execute(
            "SELECT thread_id FROM atlas_threads WHERE thread_key = ?",
            (thread_key,),
        ).fetchone()
        agent_run_id = str(uuid4())[:12]
        connection.execute(
            """
            INSERT INTO atlas_agent_runs (
                agent_run_id, thread_id, page_type, prompt, status, plan_json,
                results_json, model_mode, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                agent_run_id,
                thread["thread_id"] if thread else None,
                page_type,
                prompt,
                status,
                _json_dumps(plan or []),
                _json_dumps(results or []),
                model_mode,
                now,
                now,
            ),
        )
        connection.commit()
        return {
            "agent_run_id": agent_run_id,
            "status": status,
            "model_mode": model_mode,
            "plan": plan or [],
            "results": results or [],
        }
    finally:
        connection.close()


def list_atlas_agent_runs(thread_key=None, limit=12):
    initialize_database()
    connection = get_connection()
    try:
        if thread_key:
            rows = connection.execute(
                """
                SELECT ar.agent_run_id, ar.page_type, ar.prompt, ar.status, ar.plan_json, ar.results_json,
                       ar.model_mode, ar.created_at, ar.updated_at
                FROM atlas_agent_runs ar
                JOIN atlas_threads at ON at.thread_id = ar.thread_id
                WHERE at.thread_key = ?
                ORDER BY ar.created_at DESC
                LIMIT ?
                """,
                (thread_key, int(limit or 12)),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT agent_run_id, page_type, prompt, status, plan_json, results_json, model_mode, created_at, updated_at
                FROM atlas_agent_runs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (int(limit or 12),),
            ).fetchall()
        return [
            {
                "agent_run_id": row["agent_run_id"],
                "page_type": row["page_type"],
                "prompt": row["prompt"],
                "status": row["status"],
                "plan": _json_loads(row["plan_json"], []),
                "results": _json_loads(row["results_json"], []),
                "model_mode": row["model_mode"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]
    finally:
        connection.close()


def list_audit_events(limit=100, event_type=None):
    initialize_database()
    connection = get_connection()
    try:
        if event_type:
            rows = connection.execute(
                """
                SELECT event_id, event_type, actor_user_id, project_id, run_id, thread_id, payload_json, created_at
                FROM audit_events
                WHERE event_type = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (event_type, int(limit or 100)),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT event_id, event_type, actor_user_id, project_id, run_id, thread_id, payload_json, created_at
                FROM audit_events
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (int(limit or 100),),
            ).fetchall()
        return [
            {
                "event_id": row["event_id"],
                "event_type": row["event_type"],
                "actor_user_id": row["actor_user_id"],
                "project_id": row["project_id"],
                "run_id": row["run_id"],
                "thread_id": row["thread_id"],
                "payload": _json_loads(row["payload_json"], {}),
                "created_at": row["created_at"],
            }
            for row in rows
        ]
    finally:
        connection.close()


def list_review_decisions(project_id=None, limit=50):
    initialize_database()
    connection = get_connection()
    try:
        if project_id:
            rows = connection.execute(
                """
                SELECT decision_id, project_id, run_id, status, summary, actor_user_id, created_at
                FROM review_decisions
                WHERE project_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (project_id, int(limit or 50)),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT decision_id, project_id, run_id, status, summary, actor_user_id, created_at
                FROM review_decisions
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (int(limit or 50),),
            ).fetchall()
        return [
            {
                "decision_id": row["decision_id"],
                "project_id": row["project_id"],
                "run_id": row["run_id"],
                "status": row["status"],
                "summary": row["summary"],
                "actor_user_id": row["actor_user_id"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]
    finally:
        connection.close()


def record_evaluation_run(summary, scope="fixtures"):
    initialize_database()
    payload = summary or {}
    created_at = _now_iso()
    connection = get_connection()
    try:
        evaluation_id = str(uuid4())[:12]
        connection.execute(
            """
            INSERT INTO evaluation_runs (
                evaluation_id, scope, fixture_count, average_score, average_parser_confidence,
                failed_board_count, summary_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evaluation_id,
                scope,
                int(payload.get("fixture_count") or 0),
                float(payload.get("average_score") or 0.0),
                float(payload.get("average_parser_confidence") or 0.0),
                int(payload.get("failed_board_count") or 0),
                _json_dumps(payload),
                created_at,
            ),
        )
        connection.commit()
        return {
            "evaluation_id": evaluation_id,
            "scope": scope,
            "fixture_count": int(payload.get("fixture_count") or 0),
            "average_score": float(payload.get("average_score") or 0.0),
            "average_parser_confidence": float(payload.get("average_parser_confidence") or 0.0),
            "failed_board_count": int(payload.get("failed_board_count") or 0),
            "created_at": created_at,
        }
    finally:
        connection.close()


def list_evaluation_runs(limit=12):
    initialize_database()
    connection = get_connection()
    try:
        rows = connection.execute(
            """
            SELECT evaluation_id, scope, fixture_count, average_score, average_parser_confidence,
                   failed_board_count, summary_json, created_at
            FROM evaluation_runs
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (int(limit or 12),),
        ).fetchall()
        return [
            {
                "evaluation_id": row["evaluation_id"],
                "scope": row["scope"],
                "fixture_count": row["fixture_count"],
                "average_score": row["average_score"],
                "average_parser_confidence": row["average_parser_confidence"],
                "failed_board_count": row["failed_board_count"],
                "summary": _json_loads(row["summary_json"], {}),
                "created_at": row["created_at"],
            }
            for row in rows
        ]
    finally:
        connection.close()


def upsert_integration_config(integration_type, label, status="configured", config=None, created_by_user_id=None):
    initialize_database()
    normalized_type = str(integration_type or "").strip().lower()
    if not normalized_type:
        raise ValueError("integration_type is required")
    now = _now_iso()
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT integration_id FROM integration_configs WHERE integration_type = ?",
            (normalized_type,),
        ).fetchone()
        if row:
            integration_id = row["integration_id"]
            connection.execute(
                """
                UPDATE integration_configs
                SET label = ?, status = ?, config_json = ?, updated_at = ?
                WHERE integration_id = ?
                """,
                (label, status, _json_dumps(config), now, integration_id),
            )
        else:
            integration_id = str(uuid4())[:12]
            connection.execute(
                """
                INSERT INTO integration_configs (
                    integration_id, integration_type, label, status, config_json,
                    created_by_user_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    integration_id,
                    normalized_type,
                    label,
                    status,
                    _json_dumps(config),
                    created_by_user_id,
                    now,
                    now,
                ),
            )
        connection.commit()
        return {
            "integration_id": integration_id,
            "integration_type": normalized_type,
            "label": label,
            "status": status,
            "config": config or {},
            "updated_at": now,
        }
    finally:
        connection.close()


def list_integration_configs():
    initialize_database()
    connection = get_connection()
    try:
        rows = connection.execute(
            """
            SELECT integration_id, integration_type, label, status, config_json, created_at, updated_at
            FROM integration_configs
            ORDER BY integration_type ASC
            """
        ).fetchall()
        return [
            {
                "integration_id": row["integration_id"],
                "integration_type": row["integration_type"],
                "label": row["label"],
                "status": row["status"],
                "config": _json_loads(row["config_json"], {}),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]
    finally:
        connection.close()


initialize_database()
