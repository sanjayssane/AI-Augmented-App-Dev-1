"""PlatformSettings ORM model."""

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PlatformSettings(Base):
    __tablename__ = "platform_settings"

    setting_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    setting_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
