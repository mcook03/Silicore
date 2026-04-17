import threading
import time
from datetime import datetime, timezone
from uuid import uuid4

from engine.job_runner import process_queued_jobs
from engine.runtime_config import get_runtime_config


_worker_thread = None
_worker_stop_event = None
_worker_lock = threading.Lock()
_worker_state = {
    "worker_id": None,
    "poll_seconds": None,
    "started_at": None,
    "last_tick_at": None,
    "last_processed_count": 0,
}


def _now_text():
    return time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())


def _worker_loop(interval_seconds, worker_id, batch_size, lease_seconds):
    global _worker_stop_event
    _worker_state["worker_id"] = worker_id
    _worker_state["poll_seconds"] = interval_seconds
    _worker_state["started_at"] = _now_text()
    while _worker_stop_event and not _worker_stop_event.is_set():
        processed = process_queued_jobs(limit=batch_size, worker_id=worker_id, lease_seconds=lease_seconds)
        _worker_state["last_tick_at"] = _now_text()
        _worker_state["last_processed_count"] = len(processed)
        _worker_stop_event.wait(interval_seconds)


def start_worker(interval_seconds=None, batch_size=None, lease_seconds=None):
    global _worker_thread, _worker_stop_event
    runtime = get_runtime_config()
    poll_seconds = float(interval_seconds or runtime["worker_poll_seconds"])
    batch = int(batch_size or runtime["worker_batch_size"])
    lease = int(lease_seconds or runtime["job_lease_seconds"])
    with _worker_lock:
        if _worker_thread and _worker_thread.is_alive():
            return {"status": "running", **worker_status()}
        _worker_stop_event = threading.Event()
        worker_id = f"silicore-worker-{str(uuid4())[:8]}"
        _worker_thread = threading.Thread(
            target=_worker_loop,
            args=(poll_seconds, worker_id, batch, lease),
            daemon=True,
            name=worker_id,
        )
        _worker_thread.start()
        return {"status": "started", **worker_status()}


def stop_worker():
    global _worker_thread, _worker_stop_event
    with _worker_lock:
        if _worker_stop_event:
            _worker_stop_event.set()
        if _worker_thread and _worker_thread.is_alive():
            _worker_thread.join(timeout=1.0)
        _worker_thread = None
        _worker_stop_event = None
        _worker_state.update(
            {
                "worker_id": None,
                "poll_seconds": None,
                "started_at": None,
                "last_tick_at": None,
                "last_processed_count": 0,
            }
        )
        return {"status": "stopped"}


def worker_status():
    thread = _worker_thread
    runtime = get_runtime_config()
    last_tick = _worker_state["last_tick_at"]
    stale = False
    if last_tick:
        try:
            last_tick_dt = datetime.strptime(last_tick, "%Y-%m-%d %H:%M:%S UTC").replace(tzinfo=timezone.utc)
            stale = (datetime.now(timezone.utc) - last_tick_dt).total_seconds() > float(runtime["worker_stale_seconds"])
        except ValueError:
            stale = False
    return {
        "running": bool(thread and thread.is_alive()),
        "thread_name": getattr(thread, "name", None),
        "worker_id": _worker_state["worker_id"],
        "poll_seconds": _worker_state["poll_seconds"],
        "started_at": _worker_state["started_at"],
        "last_tick_at": _worker_state["last_tick_at"],
        "last_processed_count": _worker_state["last_processed_count"],
        "stale": stale,
        "healthy": bool(thread and thread.is_alive()) and not stale,
    }
