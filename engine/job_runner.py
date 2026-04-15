from engine.atlas_tools import create_signoff_packet
from engine.evaluation_backend import run_evaluation_job
from engine.job_store import list_jobs, update_job


def process_queued_jobs(limit=10):
    processed = []
    for job in list_jobs(limit=limit):
        if job.get("status") != "queued":
            continue
        job_type = job.get("job_type")
        payload = job.get("payload") or {}
        if job_type == "evaluation_suite":
            try:
                result = run_evaluation_job(
                    job["job_id"],
                    fixtures_dir=payload.get("fixtures_dir", "fixtures"),
                    config=payload.get("config", "custom_config.json"),
                )
                processed.append({"job_id": job["job_id"], "status": "completed", "result": result})
            except Exception as exc:
                update_job(job["job_id"], status="failed", error_text=str(exc))
                processed.append({"job_id": job["job_id"], "status": "failed", "error": str(exc)})
        elif job_type == "signoff_packet":
            try:
                payload = job.get("payload") or {}
                result = create_signoff_packet(payload.get("context") or {})
                update_job(job["job_id"], status="completed", result=result)
                processed.append({"job_id": job["job_id"], "status": "completed", "result": result})
            except Exception as exc:
                update_job(job["job_id"], status="failed", error_text=str(exc))
                processed.append({"job_id": job["job_id"], "status": "failed", "error": str(exc)})
        else:
            update_job(job["job_id"], status="failed", error_text=f"No runner for job type: {job_type}")
            processed.append({"job_id": job["job_id"], "status": "failed", "error": f"No runner for job type: {job_type}"})
    return processed
