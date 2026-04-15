from uuid import uuid4

from engine.db import get_connection, initialize_database, log_audit_event


def _now(connection):
    return connection.execute("SELECT strftime('%Y-%m-%d %H:%M:%S', 'now') || ' UTC'").fetchone()[0]


def create_organization(name):
    initialize_database()
    connection = get_connection()
    try:
        organization_key = str(uuid4())[:8]
        now = _now(connection)
        connection.execute(
            """
            INSERT INTO organizations (organization_key, name, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (organization_key, (name or "").strip() or "Engineering Workspace", now, now),
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
            SELECT organization_key, name, created_at, updated_at
            FROM organizations
            WHERE organization_key = ?
            """,
            (organization_key,),
        ).fetchone()
        if not row:
            return None
        return {
            "organization_key": row["organization_key"],
            "name": row["name"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
    finally:
        connection.close()


def list_organizations():
    initialize_database()
    connection = get_connection()
    try:
        rows = connection.execute(
            """
            SELECT organization_key, name, created_at, updated_at
            FROM organizations
            ORDER BY created_at ASC
            """
        ).fetchall()
        return [
            {
                "organization_key": row["organization_key"],
                "name": row["name"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]
    finally:
        connection.close()
