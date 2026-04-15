import os
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage


OUTBOX_DIR = os.getenv("SILICORE_OUTBOX_DIR", "dashboard_outbox")


def _now_stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def _email_config():
    return {
        "host": os.getenv("SILICORE_SMTP_HOST") or os.getenv("SMTP_HOST"),
        "port": int(os.getenv("SILICORE_SMTP_PORT") or os.getenv("SMTP_PORT") or 587),
        "username": os.getenv("SILICORE_SMTP_USERNAME") or os.getenv("SMTP_USERNAME"),
        "password": os.getenv("SILICORE_SMTP_PASSWORD") or os.getenv("SMTP_PASSWORD"),
        "sender": os.getenv("SILICORE_EMAIL_SENDER") or "noreply@silicore.local",
        "tls": str(os.getenv("SILICORE_SMTP_TLS", "true")).strip().lower() in {"1", "true", "yes", "on"},
        "enabled": bool(os.getenv("SILICORE_SMTP_HOST") or os.getenv("SMTP_HOST")),
    }


def send_email(recipient, subject, body):
    config = _email_config()
    recipient = str(recipient or "").strip()
    if not recipient:
        return {"status": "skipped", "reason": "missing_recipient"}

    if config["enabled"]:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = config["sender"]
        message["To"] = recipient
        message.set_content(body)
        with smtplib.SMTP(config["host"], config["port"], timeout=15) as smtp:
            if config["tls"]:
                smtp.starttls()
            if config["username"]:
                smtp.login(config["username"], config["password"] or "")
            smtp.send_message(message)
        return {"status": "sent", "transport": "smtp"}

    os.makedirs(OUTBOX_DIR, exist_ok=True)
    path = os.path.join(OUTBOX_DIR, f"{_now_stamp()}_{recipient.replace('@', '_at_')}.txt")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(f"To: {recipient}\n")
        handle.write(f"Subject: {subject}\n\n")
        handle.write(body)
    return {"status": "queued", "transport": "outbox", "path": path}


def send_identity_email(recipient, email_type, token, context=None):
    context = context or {}
    subject_map = {
        "verification": "Silicore email verification",
        "password_reset": "Silicore password reset",
        "mfa": "Silicore multi-factor verification",
        "organization_invite": "Silicore organization invitation",
    }
    body_map = {
        "verification": (
            "Silicore verification was requested for your account.\n\n"
            f"Verification token: {token}\n"
            f"Workspace: {context.get('organization_name', 'Silicore Nexus')}\n"
        ),
        "password_reset": (
            "Silicore password reset was requested.\n\n"
            f"Reset token: {token}\n"
        ),
        "mfa": (
            "Silicore multi-factor verification is required.\n\n"
            f"Challenge token: {context.get('challenge_token', '')}\n"
            f"Verification code: {token}\n"
        ),
        "organization_invite": (
            f"You were invited to join {context.get('organization_name', 'Silicore Nexus')}.\n\n"
            f"Invitation token: {token}\n"
            f"Invited role: {context.get('invited_role', 'engineer')}\n"
        ),
    }
    return send_email(
        recipient,
        subject_map.get(email_type, "Silicore notification"),
        body_map.get(email_type, f"Token: {token}"),
    )
