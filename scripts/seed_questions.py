#!/usr/bin/env python3
"""Seed question bank with sample MCQs (Phase 4+ — not implemented)."""

from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seed at least 55 active questions for staging/dev.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=55,
        help="Number of questions to seed (default: 55)",
    )
    args = parser.parse_args()

    _ = args
    print("Phase 1+ — seed_questions is not implemented yet.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
