"""User ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.erasure import ErasureJob
    from app.models.question import Question, QuestionVersion
    from app.models.session import TestSession


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "(role = 'EXAMINER' AND username IS NOT NULL AND password_hash IS NOT NULL "
            "AND prn_ciphertext IS NULL AND prn_lookup_hash IS NULL AND name_ciphertext IS NULL) "
            "OR (role = 'EXAMINEE' AND username IS NULL AND password_hash IS NULL "
            "AND prn_ciphertext IS NOT NULL AND prn_lookup_hash IS NOT NULL "
            "AND name_ciphertext IS NOT NULL)",
            name="ck_users_role_fields",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    prn_ciphertext: Mapped[str | None] = mapped_column(Text, nullable=True)
    prn_lookup_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    name_ciphertext: Mapped[str | None] = mapped_column(Text, nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=True, create_constraint=True),
        nullable=False,
    )
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    privacy_acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    test_sessions: Mapped[list[TestSession]] = relationship(back_populates="user")
    questions_created: Mapped[list[Question]] = relationship(
        back_populates="created_by_user",
        foreign_keys="Question.created_by",
    )
    question_versions_modified: Mapped[list[QuestionVersion]] = relationship(
        back_populates="modified_by_user",
        foreign_keys="QuestionVersion.modified_by",
    )
    erasure_jobs_as_examinee: Mapped[list[ErasureJob]] = relationship(
        back_populates="examinee",
        foreign_keys="ErasureJob.examinee_user_id",
    )
    erasure_jobs_as_operator: Mapped[list[ErasureJob]] = relationship(
        back_populates="operator",
        foreign_keys="ErasureJob.operator_user_id",
    )
