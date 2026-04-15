from datetime import datetime, timedelta, timezone
from uuid import uuid4

from engine.db import get_connection, initialize_database, log_audit_event
from engine.user_store import get_user_by_email, get_user_by_id


def _now(connection=None):
    if connection is not None:
        return connection.execute("SELECT strftime('%Y-%m-%d %H:%M:%S', 'now') || ' UTC'").fetchone()[0]
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _row_to_org(row):
    if not row:
        return None
    import json

    return {
        "organization_key": row["organization_key"],
        "name": row["name"],
        "domain": row["domain"],
        "security": json.loads(row["security_json"] or "{}"),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def create_organization(name, domain=None, security=None):
    import json

    initialize_database()
    connection = get_connection()
    try:
        organization_key = str(uuid4())[:8]
        now = _now(connection)
        security = security or {
            "require_verified_email": False,
            "enforce_mfa_for_leads": False,
            "allow_self_signup": True,
        }
        connection.execute(
            """
            INSERT INTO organizations (organization_key, name, domain, security_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (organization_key, (name or "").strip() or "Engineering Workspace", (domain or "").strip().lower() or None, json.dumps(security, sort_keys=True), now, now),
        )
        connection.commit()
    finally:
        connection.close()
    log_audit_event("organization.created", payload={"organization_key": organization_key, "name": name})
    return get_organization(organization_key)


def get_organization(organization_key):
    initialize_database()
    connection = get_connection()
    try:
        row = connection.execute(
            """
            SELECT organization_key, name, domain, security_json, created_at, updated_at
            FROM organizations
            WHERE organization_key = ?
            """,
            (organization_key,),
        ).fetchone()
        return _row_to_org(row)
    finally:
        connection.close()


def list_organizations():
    initialize_database()
    connection = get_connection()
    try:
        rows = connection.execute(
            """
            SELECT organization_key, name, domain, security_json, created_at, updated_at
            FROM organizations
            ORDER BY created_at ASC
            """
        ).fetchall()
        return [_row_to_org(row) for row in rows]
    finally:
        connection.close()


def update_organization_security(organization_key, security):
    import json

    initialize_database()
    connection = get_connection()
    try:
        now = _now(connection)
        connection.execute(
            "UPDATE organizations SET security_json = ?, updated_at = ? WHERE organization_key = ?",
            (json.dumps(security or {}, sort_keys=True), now, organization_key),
        )
        connection.commit()
    finally:
        connection.close()
    log_audit_event("organization.security_updated", payload={"organization_key": organization_key})
    return get_organization(organization_key)


def create_organization_invitation(organization_key, email, invited_role="engineer", invited_by_user_id=None):
    initialize_database()
    normalized_email = str(email or "").strip().lower()
    connection = get_connection()
    try:
        invitation_id = str(uuid4())[:12]
        token = uuid4().hex
        created_at = datetime.now(timezone.utc)
        expires_at = created_at + timedelta(days=7)
        connection.execute(
            """
            INSERT INTO organization_invitations (
                invitation_id, organization_key, email, invited_role, token, status,
                invited_by_user_id, accepted_user_id, created_at, expires_at, accepted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                invitation_id,
                organization_key,
                normalized_email,
                invited_role,
                token,
                "pending",
                invited_by_user_id,
                None,
                created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                expires_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                None,
            ),
        )
        connection.commit()
    finally:
        connection.close()
    log_audit_event("organization.invitation_created", actor_user_id=invited_by_user_id, payload={"organization_key": organization_key, "email": normalized_email})
    return {"token": token, "email": normalized_email, "organization_key": organization_key, "invited_role": invited_role}


def list_organization_invitations(organization_key, status=None):
    initialize_database()
    connection = get_connection()
    try:
        if status:
            rows = connection.execute(
                """
                SELECT invitation_id, organization_key, email, invited_role, token, status,
                       invited_by_user_id, accepted_user_id, created_at, expires_at, accepted_at
                FROM organization_invitations
                WHERE organization_key = ? AND status = ?
                ORDER BY created_at DESC
                """,
                (organization_key, status),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT invitation_id, organization_key, email, invited_role, token, status,
                       invited_by_user_id, accepted_user_id, created_at, expires_at, accepted_at
                FROM organization_invitations
                WHERE organization_key = ?
                ORDER BY created_at DESC
                """,
                (organization_key,),
            ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def accept_organization_invitation(token, accepted_user_id=None):
    if not token:
        return None
    initialize_database()
    connection = get_connection()
    row = None
    try:
        row = connection.execute(
            """
            SELECT invitation_id, organization_key, email, invited_role, status, expires_at
            FROM organization_invitations
            WHERE token = ?
            """,
            (token,),
        ).fetchone()
        if not row or row["status"] != "pending":
            return None
        expires_at = datetime.strptime(row["expires_at"], "%Y-%m-%d %H:%M:%S UTC").replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            return None
        if accepted_user_id:
            connection.execute(
                "UPDATE users SET organization_key = ?, updated_at = ? WHERE user_id = ?",
                (row["organization_key"], _now(connection), accepted_user_id),
            )
        connection.execute(
            """
            UPDATE organization_invitations
            SET status = 'accepted', accepted_user_id = ?, accepted_at = ?
            WHERE invitation_id = ?
            """,
            (accepted_user_id, _now(connection), row["invitation_id"]),
        )
        connection.commit()
    finally:
        connection.close()
    log_audit_event("organization.invitation_accepted", actor_user_id=accepted_user_id, payload={"organization_key": row["organization_key"] if row else None, "email": row["email"] if row else None})
    return {"organization_key": row["organization_key"], "invited_role": row["invited_role"], "email": row["email"]} if row else None
