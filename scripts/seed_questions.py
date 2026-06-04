#!/usr/bin/env python3
"""Seed question bank with sample MCQs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import create_engine, func, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.models.enums import CorrectOption, UserRole  # noqa: E402
from app.models.question import Question  # noqa: E402
from app.models.user import User  # noqa: E402

OPTIONS = ("A", "B", "C", "D")


def _sample_question(index: int) -> dict:
    correct = OPTIONS[index % 4]
    return {
        "question_text": f"Sample question {index}: What is 2 + 2?",
        "option_a": "3",
        "option_b": "4",
        "option_c": "5",
        "option_d": "6",
        "correct_option": CorrectOption(correct),
    }


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
    parser.add_argument(
        "--examiner-username",
        default="admin",
        help="Examiner username for created_by (default: admin)",
    )
    args = parser.parse_args()

    if args.count < 55:
        print("PRD requires at least 55 questions in the bank.", file=sys.stderr)
        return 1

    engine = create_engine(settings.database_url, pool_pre_ping=True)
    with Session(engine) as session:
        examiner = session.scalar(
            select(User).where(
                User.username == args.examiner_username,
                User.role == UserRole.EXAMINER,
            )
        )
        if examiner is None:
            print(
                f"Examiner '{args.examiner_username}' not found. "
                "Run bootstrap_examiner.py first.",
                file=sys.stderr,
            )
            return 1

        active_count = session.scalar(
            select(func.count())
            .select_from(Question)
            .where(Question.is_deleted.is_(False))
        )
        active_count = int(active_count or 0)
        needed = max(0, args.count - active_count)
        if needed == 0:
            print(f"Bank already has {active_count} active questions (>= {args.count}).")
            return 0

        for i in range(needed):
            payload = _sample_question(active_count + i + 1)
            session.add(
                Question(
                    **payload,
                    created_by=examiner.user_id,
                    question_version=1,
                    is_deleted=False,
                )
            )
        session.commit()
        print(f"Seeded {needed} questions (total active target: {args.count}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
