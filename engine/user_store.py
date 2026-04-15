from uuid import uuid4

from werkzeug.security import check_password_hash, generate_password_hash

from engine.db import get_connection, initialize_database, log_audit_event


def _row_to_user(row):
    if not row:
        return None
    return {
        "user_id": row["user_id"],
        "name": row["name"],
        "email": row["email"],
        "password_hash": row["password_hash"],
        "role": row["role"],
        "organization_key": row["organization_key"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_users():
    initialize_database()
    connection = get_connection()
    try:
        rows = connection.execute(
            """
            SELECT user_id, name, email, password_hash, role, organization_key, created_at, updated_at
            FROM users
            ORDER BY created_at ASC
            """
        ).fetchall()
        return [_row_to_user(row) for row in rows]
    finally:
        connection.close()


def get_user_by_email(email):
    initialize_database()
    normalized = str(email or "").strip().lower()
    connection = get_connection()
    try:
        row = connection.execute(
            """
            SELECT user_id, name, email, password_hash, role, organization_key, created_at, updated_at
            FROM users
            WHERE email = ?
            """,
            (normalized,),
        ).fetchone()
        return _row_to_user(row)
    finally:
        connection.close()


def get_user_by_id(user_id):
    initialize_database()
    normalized = str(user_id or "").strip()
    connection = get_connection()
    try:
        row = connection.execute(
            """
            SELECT user_id, name, email, password_hash, role, organization_key, created_at, updated_at
            FROM users
            WHERE user_id = ?
            """,
            (normalized,),
        ).fetchone()
        return _row_to_user(row)
    finally:
        connection.close()


def create_user(name, email, password):
    initialize_database()
    normalized_email = str(email or "").strip().lower()
    if not normalized_email or not password:
        raise ValueError("Email and password are required.")
    if get_user_by_email(normalized_email):
        raise ValueError("An account with that email already exists.")

    user = {
        "user_id": str(uuid4())[:10],
        "name": str(name or "").strip() or normalized_email.split("@")[0].title(),
        "email": normalized_email,
        "password_hash": generate_password_hash(password),
        "role": "engineer",
        "organization_key": "personal",
    }

    connection = get_connection()
    try:
        now = connection.execute("SELECT strftime('%Y-%m-%d %H:%M:%S', 'now') || ' UTC'").fetchone()[0]
        connection.execute(
            """
            INSERT INTO users (
                user_id, name, email, password_hash, role, organization_key, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user["user_id"],
                user["name"],
                user["email"],
                user["password_hash"],
                user["role"],
                user["organization_key"],
                now,
                now,
            ),
        )
        connection.commit()
    finally:
        connection.close()

    created = get_user_by_id(user["user_id"])
    log_audit_event("user.created", actor_user_id=user["user_id"], payload={"email": normalized_email})
    return created


def authenticate_user(email, password):
    user = get_user_by_email(email)
    if not user:
        return None
    if not check_password_hash(user.get("password_hash", ""), password or ""):
        return None
    log_audit_event("user.authenticated", actor_user_id=user["user_id"], payload={"email": user["email"]})
    return user
