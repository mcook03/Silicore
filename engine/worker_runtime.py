import threading
import time

from engine.job_runner import process_queued_jobs


_worker_thread = None
_worker_stop_event = None
_worker_lock = threading.Lock()


def _worker_loop(interval_seconds):
    global _worker_stop_event
    while _worker_stop_event and not _worker_stop_event.is_set():
        process_queued_jobs(limit=10)
        _worker_stop_event.wait(interval_seconds)


def start_worker(interval_seconds=2.0):
    global _worker_thread, _worker_stop_event
    with _worker_lock:
        if _worker_thread and _worker_thread.is_alive():
            return {"status": "running"}
        _worker_stop_event = threading.Event()
        _worker_thread = threading.Thread(
            target=_worker_loop,
            args=(float(interval_seconds or 2.0),),
            daemon=True,
            name="silicore-worker",
        )
        _worker_thread.start()
        return {"status": "started"}


def stop_worker():
    global _worker_thread, _worker_stop_event
    with _worker_lock:
        if _worker_stop_event:
            _worker_stop_event.set()
        if _worker_thread and _worker_thread.is_alive():
            _worker_thread.join(timeout=1.0)
        _worker_thread = None
        _worker_stop_event = None
        return {"status": "stopped"}


def worker_status():
    thread = _worker_thread
    return {
        "running": bool(thread and thread.is_alive()),
        "thread_name": getattr(thread, "name", None),
    }
