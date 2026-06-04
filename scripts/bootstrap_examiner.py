#!/usr/bin/env python3
"""Bootstrap first Examiner account."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.passwords import hash_password  # noqa: E402
from app.models.enums import UserRole  # noqa: E402
from app.models.user import User  # noqa: E402

MIN_PASSWORD_LEN = 12


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create the initial Examiner account for the MCQ platform.",
    )
    parser.add_argument("--username", required=True, help="Examiner username")
    parser.add_argument("--password", required=True, help="Examiner password (min 12 chars per PRD)")
    args = parser.parse_args()

    if len(args.password) < MIN_PASSWORD_LEN:
        print(f"Password must be at least {MIN_PASSWORD_LEN} characters.", file=sys.stderr)
        return 1

    engine = create_engine(settings.database_url, pool_pre_ping=True)
    with Session(engine) as session:
        existing = session.scalar(
            select(User).where(User.username == args.username, User.role == UserRole.EXAMINER)
        )
        if existing:
            print(f"Examiner '{args.username}' already exists (user_id={existing.user_id}).")
            return 0

        user = User(
            username=args.username,
            role=UserRole.EXAMINER,
            password_hash=hash_password(args.password),
            is_active=True,
        )
        session.add(user)
        session.commit()
        print(f"Created examiner '{args.username}' (user_id={user.user_id}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
