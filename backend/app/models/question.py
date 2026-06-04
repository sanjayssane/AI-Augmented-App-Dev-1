"""Question and QuestionVersion ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import CorrectOption

if TYPE_CHECKING:
    from app.models.session import Response, SessionQuestion
    from app.models.user import User


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (
        CheckConstraint("char_length(question_text) <= 2000", name="ck_questions_text_len"),
        CheckConstraint("char_length(option_a) <= 500", name="ck_questions_option_a_len"),
        CheckConstraint("char_length(option_b) <= 500", name="ck_questions_option_b_len"),
        CheckConstraint("char_length(option_c) <= 500", name="ck_questions_option_c_len"),
        CheckConstraint("char_length(option_d) <= 500", name="ck_questions_option_d_len"),
        Index("ix_questions_is_deleted_question_id", "is_deleted", "question_id"),
    )

    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    option_a: Mapped[str] = mapped_column(Text, nullable=False)
    option_b: Mapped[str] = mapped_column(Text, nullable=False)
    option_c: Mapped[str] = mapped_column(Text, nullable=False)
    option_d: Mapped[str] = mapped_column(Text, nullable=False)
    correct_option: Mapped[CorrectOption] = mapped_column(
        Enum(CorrectOption, name="correct_option", native_enum=True, create_constraint=True),
        nullable=False,
    )
    question_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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

    created_by_user: Mapped[User] = relationship(
        back_populates="questions_created",
        foreign_keys=[created_by],
    )
    versions: Mapped[list[QuestionVersion]] = relationship(back_populates="question")
    session_questions: Mapped[list[SessionQuestion]] = relationship(back_populates="question")
    responses: Mapped[list[Response]] = relationship(back_populates="question")


class QuestionVersion(Base):
    __tablename__ = "question_versions"
    __table_args__ = (
        UniqueConstraint(
            "question_id",
            "version_number",
            name="uq_question_versions_question_version",
        ),
        CheckConstraint(
            "char_length(question_text) <= 2000",
            name="ck_question_versions_text_len",
        ),
    )

    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.question_id"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    option_a: Mapped[str] = mapped_column(String(500), nullable=False)
    option_b: Mapped[str] = mapped_column(String(500), nullable=False)
    option_c: Mapped[str] = mapped_column(String(500), nullable=False)
    option_d: Mapped[str] = mapped_column(String(500), nullable=False)
    correct_option: Mapped[CorrectOption] = mapped_column(
        Enum(CorrectOption, name="correct_option", native_enum=True, create_constraint=False),
        nullable=False,
    )
    modified_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    question: Mapped[Question] = relationship(back_populates="versions")
    modified_by_user: Mapped[User] = relationship(
        back_populates="question_versions_modified",
        foreign_keys=[modified_by],
    )
