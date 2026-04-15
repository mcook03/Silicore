import json
import os
import uuid
from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

USERS_FOLDER = "dashboard_users"
USERS_FILE = os.path.join(USERS_FOLDER, "users.json")


def ensure_users_store():
    os.makedirs(USERS_FOLDER, exist_ok=True)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as file:
            json.dump({"users": []}, file, indent=2)


def _load_users():
    ensure_users_store()
    with open(USERS_FILE, "r", encoding="utf-8") as file:
        payload = json.load(file)
    return payload.get("users", []) or []


def _save_users(users):
    ensure_users_store()
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump({"users": users}, file, indent=2)


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def list_users():
    return _load_users()


def get_user_by_email(email):
    normalized = str(email or "").strip().lower()
    for user in _load_users():
        if str(user.get("email") or "").strip().lower() == normalized:
            return user
    return None


def get_user_by_id(user_id):
    normalized = str(user_id or "").strip()
    for user in _load_users():
        if str(user.get("user_id") or "").strip() == normalized:
            return user
    return None


def create_user(name, email, password):
    users = _load_users()
    normalized_email = str(email or "").strip().lower()
    if not normalized_email or not password:
        raise ValueError("Email and password are required.")
    if get_user_by_email(normalized_email):
        raise ValueError("An account with that email already exists.")

    user = {
        "user_id": str(uuid.uuid4())[:10],
        "name": str(name or "").strip() or normalized_email.split("@")[0].title(),
        "email": normalized_email,
        "password_hash": generate_password_hash(password),
        "created_at": _now_iso(),
    }
    users.append(user)
    _save_users(users)
    return user


def authenticate_user(email, password):
    user = get_user_by_email(email)
    if not user:
        return None
    if not check_password_hash(user.get("password_hash", ""), password or ""):
        return None
    return user
