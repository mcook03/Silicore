import os


def _env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name, default):
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return int(default)


def _env_float(name, default):
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return float(default)


def get_runtime_config():
    return {
        "environment": os.getenv("SILICORE_ENV", "development"),
        "host": os.getenv("SILICORE_HOST", "127.0.0.1"),
        "port": _env_int("SILICORE_PORT", 5001),
        "debug": _env_bool("SILICORE_DEBUG", False),
        "worker_autostart": _env_bool("SILICORE_WORKER_AUTOSTART", False),
        "worker_poll_seconds": _env_float("SILICORE_WORKER_POLL_SECONDS", 2.0),
        "worker_batch_size": _env_int("SILICORE_WORKER_BATCH_SIZE", 10),
        "worker_stale_seconds": _env_int("SILICORE_WORKER_STALE_SECONDS", 30),
        "job_lease_seconds": _env_int("SILICORE_JOB_LEASE_SECONDS", 90),
        "job_max_attempts": _env_int("SILICORE_JOB_MAX_ATTEMPTS", 3),
        "session_days": _env_int("SILICORE_SESSION_DAYS", 14),
        "database_path": os.getenv("SILICORE_DB_PATH"),
        "secret_configured": bool(os.getenv("SILICORE_SECRET_KEY") or os.getenv("FLASK_SECRET_KEY")),
    }
