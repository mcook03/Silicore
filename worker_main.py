import argparse
import time

from engine.job_runner import process_queued_jobs
from engine.runtime_config import get_runtime_config


def main():
    runtime = get_runtime_config()
    parser = argparse.ArgumentParser(description="Run the Silicore backend worker.")
    parser.add_argument("--once", action="store_true", help="Process one batch and exit.")
    parser.add_argument("--poll-seconds", type=float, default=runtime["worker_poll_seconds"])
    parser.add_argument("--batch-size", type=int, default=runtime["worker_batch_size"])
    parser.add_argument("--lease-seconds", type=int, default=runtime["job_lease_seconds"])
    parser.add_argument("--worker-id", default="silicore-service-worker")
    args = parser.parse_args()

    if args.once:
        processed = process_queued_jobs(limit=args.batch_size, worker_id=args.worker_id, lease_seconds=args.lease_seconds)
        print(f"Processed {len(processed)} job(s).")
        return

    print(f"Silicore worker started as {args.worker_id}. Polling every {args.poll_seconds} seconds.")
    while True:
        process_queued_jobs(limit=args.batch_size, worker_id=args.worker_id, lease_seconds=args.lease_seconds)
        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    main()
