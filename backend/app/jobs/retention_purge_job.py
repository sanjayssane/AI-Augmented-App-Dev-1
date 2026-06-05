"""Background job: purge completed sessions after retention window."""

from __future__ import annotations

from app.core.database import SessionLocal
from app.repositories.platform_settings_repository import PlatformSettingsRepository
from app.repositories.test_session_repository import TestSessionRepository
from app.services.retention_job_service import RetentionJobService


def run() -> int:
    with SessionLocal() as db:
        service = RetentionJobService(
            db=db,
            session_repo=TestSessionRepository(),
            settings_repo=PlatformSettingsRepository(),
        )
        return service.purge_completed_sessions()
