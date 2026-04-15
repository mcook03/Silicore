ROLE_ORDER = {
    "viewer": 10,
    "engineer": 20,
    "lead": 30,
    "admin": 40,
}


def normalize_role(role):
    value = str(role or "viewer").strip().lower()
    return value if value in ROLE_ORDER else "viewer"


def has_role(user, minimum_role):
    user_role = normalize_role((user or {}).get("role"))
    target_role = normalize_role(minimum_role)
    return ROLE_ORDER.get(user_role, 0) >= ROLE_ORDER.get(target_role, 0)


def can_manage_project(user, project):
    if not user or not project:
        return False
    if has_role(user, "admin"):
        return True
    owner = project.get("owner") or {}
    if owner.get("user_id") == user.get("user_id"):
        return True
    for member in project.get("team_members", []) or []:
        if member.get("user_id") == user.get("user_id") and normalize_role(member.get("member_role")) in {"lead", "admin"}:
            return True
    return False


def project_is_visible_to_user(user, project):
    if not project:
        return False
    if not user:
        return True
    if has_role(user, "admin"):
        return True
    owner = project.get("owner") or {}
    if owner.get("user_id") == user.get("user_id"):
        return True
    return any(member.get("user_id") == user.get("user_id") for member in (project.get("team_members") or []))
