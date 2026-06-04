"""TestSession, SessionQuestion, and Response ORM models."""

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
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import SelectedOption, SelectionMode, SessionStatus

if TYPE_CHECKING:
    from app.models.question import Question
    from app.models.user import User


class TestSession(Base):
    __test__ = False  # prevent pytest from collecting this ORM class

    __tablename__ = "test_sessions"
    __table_args__ = (
        Index("ix_test_sessions_user_id_status", "user_id", "status"),
        Index("ix_test_sessions_status_last_activity_at", "status", "last_activity_at"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
    )
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="session_status", native_enum=True, create_constraint=True),
        nullable=False,
    )
    selection_mode: Mapped[SelectionMode] = mapped_column(
        Enum(SelectionMode, name="selection_mode", native_enum=True, create_constraint=True),
        nullable=False,
    )
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="test_sessions")
    session_questions: Mapped[list[SessionQuestion]] = relationship(back_populates="test_session")
    responses: Mapped[list[Response]] = relationship(back_populates="test_session")


class SessionQuestion(Base):
    __tablename__ = "session_questions"
    __table_args__ = (
        UniqueConstraint("session_id", "position", name="uq_session_questions_session_position"),
        UniqueConstraint("session_id", "question_id", name="uq_session_questions_session_question"),
        CheckConstraint("position >= 1 AND position <= 50", name="ck_session_questions_position"),
    )

    session_question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("test_sessions.session_id"),
        nullable=False,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.question_id"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    question_version_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)

    test_session: Mapped[TestSession] = relationship(back_populates="session_questions")
    question: Mapped[Question] = relationship(back_populates="session_questions")


class Response(Base):
    __tablename__ = "responses"
    __table_args__ = (
        UniqueConstraint("session_id", "question_id", name="uq_responses_session_question"),
    )

    response_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("test_sessions.session_id"),
        nullable=False,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.question_id"),
        nullable=False,
    )
    selected_option: Mapped[SelectedOption | None] = mapped_column(
        Enum(SelectedOption, name="selected_option", native_enum=True, create_constraint=True),
        nullable=True,
    )
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    test_session: Mapped[TestSession] = relationship(back_populates="responses")
    question: Mapped[Question] = relationship(back_populates="responses")
