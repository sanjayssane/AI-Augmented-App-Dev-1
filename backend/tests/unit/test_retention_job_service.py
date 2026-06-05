"""Unit tests for RetentionJobService."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from app.services.retention_job_service import RetentionJobService


def test_expire_abandoned_sessions_calls_repo_and_commits() -> None:
    db = MagicMock()
    session_repo = MagicMock()
    settings_repo = MagicMock()
    session_repo.expire_stale_active.return_value = 4

    service = RetentionJobService(
        db=db,
        session_repo=session_repo,
        settings_repo=settings_repo,
    )

    now = datetime(2026, 6, 5, tzinfo=UTC)
    expired = service.expire_abandoned_sessions(now=now)

    assert expired == 4
    session_repo.expire_stale_active.assert_called_once_with(db, now=now)
    db.commit.assert_called_once()


def test_purge_completed_sessions_uses_retention_setting() -> None:
    db = MagicMock()
    session_repo = MagicMock()
    settings_repo = MagicMock()
    settings_repo.get_value.return_value = 30
    session_repo.purge_completed_before.return_value = 2

    service = RetentionJobService(
        db=db,
        session_repo=session_repo,
        settings_repo=settings_repo,
    )

    now = datetime(2026, 6, 5, tzinfo=UTC)
    purged = service.purge_completed_sessions(now=now)

    assert purged == 2
    expected_before = now - timedelta(days=30)
    session_repo.purge_completed_before.assert_called_once_with(db, before=expected_before)
    db.commit.assert_called_once()


def test_purge_completed_sessions_defaults_when_setting_invalid() -> None:
    db = MagicMock()
    session_repo = MagicMock()
    settings_repo = MagicMock()
    settings_repo.get_value.return_value = "invalid"
    session_repo.purge_completed_before.return_value = 1

    service = RetentionJobService(
        db=db,
        session_repo=session_repo,
        settings_repo=settings_repo,
    )

    now = datetime(2026, 6, 5, tzinfo=UTC)
    service.purge_completed_sessions(now=now)

    expected_before = now - timedelta(days=730)
    session_repo.purge_completed_before.assert_called_once_with(db, before=expected_before)
