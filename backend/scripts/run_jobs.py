"""CLI utility to execute background jobs manually."""

from __future__ import annotations

import argparse

from app.jobs import erasure_processor_job, retention_purge_job, session_expiry_job


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run MCQ platform background jobs")
    parser.add_argument(
        "job",
        choices=["session-expiry", "retention-purge", "erasure-processor", "all"],
        help="Job name to run",
    )
    parser.add_argument(
        "--erasure-limit",
        type=int,
        default=100,
        help="Maximum pending erasure jobs to process",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    job = args.job

    if job == "session-expiry":
        count = session_expiry_job.run()
        print(f"session-expiry: expired={count}")
        return 0

    if job == "retention-purge":
        count = retention_purge_job.run()
        print(f"retention-purge: purged={count}")
        return 0

    if job == "erasure-processor":
        count = erasure_processor_job.run(limit=args.erasure_limit)
        print(f"erasure-processor: processed={count}")
        return 0

    expired = session_expiry_job.run()
    purged = retention_purge_job.run()
    processed = erasure_processor_job.run(limit=args.erasure_limit)
    print(f"all: expired={expired} purged={purged} erasure_processed={processed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
