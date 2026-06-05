"""Retention background job use cases."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.repositories.platform_settings_repository import PlatformSettingsRepository
from app.repositories.test_session_repository import TestSessionRepository


@dataclass(frozen=True)
class RetentionJobResult:
    expired_sessions: int = 0
    purged_sessions: int = 0


class RetentionJobService:
    def __init__(
        self,
        *,
        db: Session,
        session_repo: TestSessionRepository,
        settings_repo: PlatformSettingsRepository,
    ) -> None:
        self._db = db
        self._session_repo = session_repo
        self._settings_repo = settings_repo

    def expire_abandoned_sessions(self, *, now: datetime | None = None) -> int:
        at = now or datetime.now(UTC)
        expired = self._session_repo.expire_stale_active(self._db, now=at)
        self._db.commit()
        return expired

    def purge_completed_sessions(self, *, now: datetime | None = None) -> int:
        at = now or datetime.now(UTC)
        retention_days = self._retention_days_completed()
        before = at - timedelta(days=retention_days)
        purged = self._session_repo.purge_completed_before(self._db, before=before)
        self._db.commit()
        return purged

    def _retention_days_completed(self) -> int:
        value = self._settings_repo.get_value(self._db, "retention_days_completed")
        if isinstance(value, int):
            return max(0, value)
        if isinstance(value, str):
            try:
                return max(0, int(value))
            except ValueError:
                return 730
        return 730
