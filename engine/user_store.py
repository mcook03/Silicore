import json
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from werkzeug.security import check_password_hash, generate_password_hash

from engine.db import get_connection, initialize_database, log_audit_event, utc_now_text


def _now_utc():
    return datetime.now(timezone.utc)


def _now_utc_text():
    return utc_now_text()


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
        "email_verified_at": row["email_verified_at"],
        "mfa_enabled": bool(row["mfa_enabled"]),
        "mfa_secret": row["mfa_secret"],
        "session_version": row["session_version"] or 1,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _user_select_sql():
    return """
        SELECT user_id, name, email, password_hash, role, organization_key,
               email_verified_at, mfa_enabled, mfa_secret, session_version,
               created_at, updated_at
        FROM users
    """


def list_users():
    initialize_database()
    connection = get_connection()
    try:
        rows = connection.execute(f"{_user_select_sql()} ORDER BY created_at ASC").fetchall()
        return [_row_to_user(row) for row in rows]
    finally:
        connection.close()


def get_user_by_email(email):
    initialize_database()
    normalized = str(email or "").strip().lower()
    connection = get_connection()
    try:
        row = connection.execute(f"{_user_select_sql()} WHERE email = ?", (normalized,)).fetchone()
        return _row_to_user(row)
    finally:
        connection.close()


def get_user_by_id(user_id):
    initialize_database()
    normalized = str(user_id or "").strip()
    connection = get_connection()
    try:
        row = connection.execute(f"{_user_select_sql()} WHERE user_id = ?", (normalized,)).fetchone()
        return _row_to_user(row)
    finally:
        connection.close()


def create_user(name, email, password, organization_key="personal", role="engineer", email_verified=True, mfa_enabled=False):
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
        "role": role or "engineer",
        "organization_key": organization_key or "personal",
        "email_verified_at": _now_utc_text() if email_verified else None,
        "mfa_enabled": 1 if mfa_enabled else 0,
        "mfa_secret": secrets.token_hex(16) if mfa_enabled else None,
        "session_version": 1,
    }

    connection = get_connection()
    try:
        now = _now_utc_text()
        connection.execute(
            """
            INSERT INTO users (
                user_id, name, email, password_hash, role, organization_key, email_verified_at,
                mfa_enabled, mfa_secret, session_version, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user["user_id"],
                user["name"],
                user["email"],
                user["password_hash"],
                user["role"],
                user["organization_key"],
                user["email_verified_at"],
                user["mfa_enabled"],
                user["mfa_secret"],
                user["session_version"],
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


def _create_token_record(table_name, email, lifetime_hours, event_name):
    user = get_user_by_email(email)
    if not user:
        return None
    initialize_database()
    connection = get_connection()
    try:
        now = _now_utc()
        expires_at = now + timedelta(hours=lifetime_hours)
        token = uuid4().hex
        token_id = str(uuid4())[:12]
        connection.execute(
            f"""
            INSERT INTO {table_name} (
                token_id, user_id, email, token, status, created_at, expires_at, used_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                token_id,
                user["user_id"],
                user["email"],
                token,
                "active",
                now.strftime("%Y-%m-%d %H:%M:%S UTC"),
                expires_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                None,
            ),
        )
        connection.commit()
    finally:
        connection.close()
    log_audit_event(event_name, actor_user_id=user["user_id"], payload={"email": user["email"]})
    return {
        "token": token,
        "email": user["email"],
        "expires_at": expires_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


def create_password_reset_token(email):
    return _create_token_record("password_reset_tokens", email, 2, "user.password_reset_requested")


def create_email_verification_token(email):
    return _create_token_record("email_verification_tokens", email, 24, "user.email_verification_requested")


def _consume_token(table_name, token):
    initialize_database()
    connection = get_connection()
    row = None
    try:
        row = connection.execute(
            f"SELECT token_id, user_id, status, expires_at FROM {table_name} WHERE token = ?",
            (token,),
        ).fetchone()
        if not row or row["status"] != "active":
            return None
        expires_at = datetime.strptime(row["expires_at"], "%Y-%m-%d %H:%M:%S UTC").replace(tzinfo=timezone.utc)
        if expires_at < _now_utc():
            return None
        now = _now_utc_text()
        connection.execute(
            f"UPDATE {table_name} SET status = 'used', used_at = ? WHERE token_id = ?",
            (now, row["token_id"]),
        )
        connection.commit()
    finally:
        connection.close()
    return row


def reset_password_with_token(token, new_password):
    if not token or not new_password:
        return False
    row = _consume_token("password_reset_tokens", token)
    if not row:
        return False
    connection = get_connection()
    try:
        now = _now_utc_text()
        connection.execute(
            "UPDATE users SET password_hash = ?, updated_at = ? WHERE user_id = ?",
            (generate_password_hash(new_password), now, row["user_id"]),
        )
        connection.commit()
    finally:
        connection.close()
    revoke_user_sessions(row["user_id"])
    log_audit_event("user.password_reset_completed", actor_user_id=row["user_id"], payload={"token_id": row["token_id"]})
    return True


def verify_email_with_token(token):
    row = _consume_token("email_verification_tokens", token)
    if not row:
        return False
    connection = get_connection()
    try:
        now = _now_utc_text()
        connection.execute(
            "UPDATE users SET email_verified_at = ?, updated_at = ? WHERE user_id = ?",
            (now, now, row["user_id"]),
        )
        connection.commit()
    finally:
        connection.close()
    log_audit_event("user.email_verified", actor_user_id=row["user_id"], payload={"token_id": row["token_id"]})
    return True


def enable_mfa(user_id):
    initialize_database()
    connection = get_connection()
    try:
        secret = secrets.token_hex(16)
        now = _now_utc_text()
        connection.execute(
            "UPDATE users SET mfa_enabled = 1, mfa_secret = ?, updated_at = ? WHERE user_id = ?",
            (secret, now, user_id),
        )
        connection.commit()
    finally:
        connection.close()
    log_audit_event("user.mfa_enabled", actor_user_id=user_id)
    return get_user_by_id(user_id)


def create_auth_challenge(user_id, challenge_type="mfa", context=None, lifetime_minutes=10):
    user = get_user_by_id(user_id)
    if not user:
        return None
    initialize_database()
    connection = get_connection()
    try:
        now = _now_utc()
        expires_at = now + timedelta(minutes=lifetime_minutes)
        challenge_id = str(uuid4())[:12]
        token = uuid4().hex
        code = f"{secrets.randbelow(900000) + 100000}"
        connection.execute(
            """
            INSERT INTO auth_challenges (
                challenge_id, user_id, challenge_type, token, code, status, context_json,
                created_at, expires_at, consumed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                challenge_id,
                user["user_id"],
                challenge_type,
                token,
                code,
                "active",
                json.dumps(context or {}),
                now.strftime("%Y-%m-%d %H:%M:%S UTC"),
                expires_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                None,
            ),
        )
        connection.commit()
    finally:
        connection.close()
    log_audit_event("user.auth_challenge_created", actor_user_id=user["user_id"], payload={"challenge_type": challenge_type})
    return {"token": token, "code": code, "expires_at": expires_at.strftime("%Y-%m-%d %H:%M:%S UTC")}


def verify_auth_challenge(token, code):
    if not token or not code:
        return None
    initialize_database()
    connection = get_connection()
    row = None
    try:
        row = connection.execute(
            """
            SELECT challenge_id, user_id, challenge_type, code, status, expires_at
            FROM auth_challenges
            WHERE token = ?
            """,
            (token,),
        ).fetchone()
        if not row or row["status"] != "active" or str(row["code"]) != str(code).strip():
            return None
        expires_at = datetime.strptime(row["expires_at"], "%Y-%m-%d %H:%M:%S UTC").replace(tzinfo=timezone.utc)
        if expires_at < _now_utc():
            return None
        connection.execute(
            "UPDATE auth_challenges SET status = 'used', consumed_at = ? WHERE challenge_id = ?",
            (_now_utc_text(), row["challenge_id"]),
        )
        connection.commit()
    finally:
        connection.close()
    log_audit_event("user.auth_challenge_completed", actor_user_id=row["user_id"] if row else None, payload={"challenge_type": row["challenge_type"] if row else None})
    return get_user_by_id(row["user_id"]) if row else None


def create_session(user_id, ip_address=None, user_agent=None, lifetime_days=14):
    user = get_user_by_id(user_id)
    if not user:
        return None
    initialize_database()
    connection = get_connection()
    try:
        now = _now_utc()
        expires_at = now + timedelta(days=lifetime_days)
        session_id = str(uuid4())[:14]
        session_token = secrets.token_hex(24)
        connection.execute(
            """
            INSERT INTO user_sessions (
                session_id, user_id, session_token, session_version, status, ip_address, user_agent,
                created_at, expires_at, last_seen_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                user["user_id"],
                session_token,
                int(user.get("session_version") or 1),
                "active",
                ip_address,
                user_agent,
                now.strftime("%Y-%m-%d %H:%M:%S UTC"),
                expires_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            ),
        )
        connection.commit()
        return {"session_id": session_id, "session_token": session_token, "expires_at": expires_at.strftime("%Y-%m-%d %H:%M:%S UTC")}
    finally:
        connection.close()


def get_active_session(session_id, session_token):
    if not session_id or not session_token:
        return None
    initialize_database()
    connection = get_connection()
    row = None
    try:
        row = connection.execute(
            """
            SELECT us.user_id, us.session_version, us.status, us.expires_at, u.session_version AS user_session_version
            FROM user_sessions us
            JOIN users u ON u.user_id = us.user_id
            WHERE us.session_id = ? AND us.session_token = ?
            """,
            (session_id, session_token),
        ).fetchone()
        if not row or row["status"] != "active":
            return None
        expires_at = datetime.strptime(row["expires_at"], "%Y-%m-%d %H:%M:%S UTC").replace(tzinfo=timezone.utc)
        if expires_at < _now_utc():
            return None
        if int(row["session_version"] or 1) != int(row["user_session_version"] or 1):
            return None
        connection.execute(
            "UPDATE user_sessions SET last_seen_at = ? WHERE session_id = ?",
            (_now_utc_text(), session_id),
        )
        connection.commit()
    finally:
        connection.close()
    return get_user_by_id(row["user_id"]) if row else None


def revoke_user_sessions(user_id):
    initialize_database()
    connection = get_connection()
    try:
        now = _now_utc_text()
        connection.execute(
            "UPDATE users SET session_version = COALESCE(session_version, 1) + 1, updated_at = ? WHERE user_id = ?",
            (now, user_id),
        )
        connection.execute(
            "UPDATE user_sessions SET status = 'revoked' WHERE user_id = ? AND status = 'active'",
            (user_id,),
        )
        connection.commit()
    finally:
        connection.close()
    log_audit_event("user.sessions_revoked", actor_user_id=user_id)


def begin_authentication(email, password, ip_address=None, user_agent=None):
    user = authenticate_user(email, password)
    if not user:
        return {"status": "failed", "reason": "invalid_credentials"}
    if not user.get("email_verified_at"):
        verification = create_email_verification_token(user["email"])
        return {"status": "verification_required", "user": user, "verification": verification}
    if user.get("mfa_enabled"):
        challenge = create_auth_challenge(
            user["user_id"],
            challenge_type="mfa",
            context={"ip_address": ip_address, "user_agent": user_agent},
        )
        return {"status": "mfa_required", "user": user, "challenge": challenge}
    session_record = create_session(user["user_id"], ip_address=ip_address, user_agent=user_agent)
    return {"status": "authenticated", "user": user, "session": session_record}
