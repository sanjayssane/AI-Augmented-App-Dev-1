"""Test session eligibility rules (PRD §3.6)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

SESSION_ABSOLUTE_HOURS = 24
EXAMINEE_INACTIVITY_HOURS = 4


def session_expires_at(now: datetime | None = None) -> datetime:
    base = now or datetime.now(UTC)
    return base + timedelta(hours=EXAMINEE_INACTIVITY_HOURS)


def session_absolute_expires_at(start_time: datetime) -> datetime:
    return start_time + timedelta(hours=SESSION_ABSOLUTE_HOURS)


def is_session_expired(
    expires_at: datetime,
    last_activity_at: datetime,
    now: datetime | None = None,
) -> bool:
    current = now or datetime.now(UTC)
    absolute = session_absolute_expires_at(last_activity_at)
    return current >= expires_at or current >= absolute
