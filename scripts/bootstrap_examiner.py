#!/usr/bin/env python3
"""Bootstrap first Examiner account (Phase 4+ — not implemented)."""

from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create the initial Examiner account for the MCQ platform.",
    )
    parser.add_argument("--username", help="Examiner username")
    parser.add_argument("--password", help="Examiner password (min 12 chars per PRD)")
    args = parser.parse_args()

    _ = args
    print("Phase 1+ — bootstrap_examiner is not implemented yet.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
