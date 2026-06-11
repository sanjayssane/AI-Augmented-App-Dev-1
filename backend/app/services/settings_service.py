"""Platform settings read/write use cases."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.enums import SelectionMode
from app.repositories.platform_settings_repository import PlatformSettingsRepository


@dataclass
class PlatformSettingsView:
    retention_days_completed: int
    allow_examinee_retake: bool
    question_selection_mode: SelectionMode


class SettingsService:
    RETENTION_KEY = "retention_days_completed"
    RETAKE_KEY = "allow_examinee_retake"
    SELECTION_MODE_KEY = "question_selection_mode"

    def __init__(self, db: Session, settings_repo: PlatformSettingsRepository) -> None:
        self._db = db
        self._settings_repo = settings_repo

    def get_settings(self) -> PlatformSettingsView:
        retention = self._settings_repo.get_value(self._db, self.RETENTION_KEY)
        retake = self._settings_repo.get_value(self._db, self.RETAKE_KEY)
        mode = self._settings_repo.get_value(self._db, self.SELECTION_MODE_KEY)
        try:
            retention_days = int(retention) if retention is not None else 730
        except (TypeError, ValueError):
            retention_days = 730
        try:
            selection_mode = SelectionMode(
                mode if mode is not None else SelectionMode.FIXED_ORDER.value
            )
        except ValueError:
            selection_mode = SelectionMode.FIXED_ORDER
        return PlatformSettingsView(
            retention_days_completed=retention_days,
            allow_examinee_retake=bool(retake if retake is not None else False),
            question_selection_mode=selection_mode,
        )

    def get(self) -> PlatformSettingsView:
        return self.get_settings()

    def patch_settings(
        self,
        *,
        retention_days_completed: int | None = None,
        allow_examinee_retake: bool | None = None,
        question_selection_mode: SelectionMode | None = None,
    ) -> PlatformSettingsView:
        if retention_days_completed is not None:
            self._settings_repo.patch(self._db, self.RETENTION_KEY, retention_days_completed)
        if allow_examinee_retake is not None:
            self._settings_repo.patch(self._db, self.RETAKE_KEY, allow_examinee_retake)
        if question_selection_mode is not None:
            self._settings_repo.patch(self._db, self.SELECTION_MODE_KEY, question_selection_mode.value)
        self._db.commit()
        return self.get_settings()

    def patch(
        self,
        *,
        retention_days_completed: int | None = None,
        allow_examinee_retake: bool | None = None,
        question_selection_mode: SelectionMode | None = None,
    ) -> PlatformSettingsView:
        return self.patch_settings(
            retention_days_completed=retention_days_completed,
            allow_examinee_retake=allow_examinee_retake,
            question_selection_mode=question_selection_mode,
        )
