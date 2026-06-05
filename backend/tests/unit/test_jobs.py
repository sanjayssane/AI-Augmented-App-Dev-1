"""Unit tests for background job runners."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.jobs import erasure_processor_job, retention_purge_job, session_expiry_job


def test_session_expiry_job_runs_service(monkeypatch) -> None:
    db = MagicMock()
    service = MagicMock()
    service.expire_abandoned_sessions.return_value = 3
    session_local = MagicMock()
    session_local.return_value.__enter__.return_value = db

    monkeypatch.setattr(session_expiry_job, "SessionLocal", session_local)
    monkeypatch.setattr(session_expiry_job, "RetentionJobService", MagicMock(return_value=service))

    count = session_expiry_job.run()

    assert count == 3
    service.expire_abandoned_sessions.assert_called_once_with()


def test_retention_purge_job_runs_service(monkeypatch) -> None:
    db = MagicMock()
    service = MagicMock()
    service.purge_completed_sessions.return_value = 5
    session_local = MagicMock()
    session_local.return_value.__enter__.return_value = db

    monkeypatch.setattr(retention_purge_job, "SessionLocal", session_local)
    monkeypatch.setattr(retention_purge_job, "RetentionJobService", MagicMock(return_value=service))

    count = retention_purge_job.run()

    assert count == 5
    service.purge_completed_sessions.assert_called_once_with()


def test_erasure_processor_job_runs_service_with_limit(monkeypatch) -> None:
    db = MagicMock()
    service = MagicMock()
    service.process_pending_erasure_jobs.return_value = MagicMock(processed=7)
    session_local = MagicMock()
    session_local.return_value.__enter__.return_value = db

    monkeypatch.setattr(erasure_processor_job, "SessionLocal", session_local)
    monkeypatch.setattr(erasure_processor_job, "GdprService", MagicMock(return_value=service))

    count = erasure_processor_job.run(limit=50)

    assert count == 7
    service.process_pending_erasure_jobs.assert_called_once_with(limit=50)
