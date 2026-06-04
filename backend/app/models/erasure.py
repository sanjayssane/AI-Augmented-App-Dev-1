"""ErasureJob ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import ErasureJobStatus

if TYPE_CHECKING:
    from app.models.user import User


class ErasureJob(Base):
    __tablename__ = "erasure_jobs"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    examinee_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
    )
    operator_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
    )
    status: Mapped[ErasureJobStatus] = mapped_column(
        Enum(ErasureJobStatus, name="erasure_job_status", native_enum=True, create_constraint=True),
        nullable=False,
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    examinee: Mapped[User] = relationship(
        back_populates="erasure_jobs_as_examinee",
        foreign_keys=[examinee_user_id],
    )
    operator: Mapped[User] = relationship(
        back_populates="erasure_jobs_as_operator",
        foreign_keys=[operator_user_id],
    )
