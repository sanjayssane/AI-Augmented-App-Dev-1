"""Platform settings data access."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.settings import PlatformSettings


class PlatformSettingsRepository:
    def get_all(self, session: Session) -> list[PlatformSettings]:
        stmt = select(PlatformSettings).order_by(PlatformSettings.setting_key.asc())
        return list(session.scalars(stmt).all())

    def get_value(self, session: Session, setting_key: str) -> object | None:
        setting = session.get(PlatformSettings, setting_key)
        return setting.setting_value if setting is not None else None

    def patch(self, session: Session, setting_key: str, setting_value: object) -> PlatformSettings:
        setting = session.get(PlatformSettings, setting_key)
        if setting is None:
            setting = PlatformSettings(setting_key=setting_key, setting_value=setting_value)
            session.add(setting)
        else:
            setting.setting_value = setting_value
        session.flush()
        return setting
