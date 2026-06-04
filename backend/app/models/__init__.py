"""
SQLAlchemy ORM models (Phase 1).

Declarative Base and entity models per docs/MCQ_Platform_ERD.md.
"""

from app.models.audit import AuditLog
from app.models.base import Base
from app.models.enums import (
    AuditOutcome,
    CorrectOption,
    ErasureJobStatus,
    SelectedOption,
    SelectionMode,
    SessionStatus,
    UserRole,
)
from app.models.erasure import ErasureJob
from app.models.question import Question, QuestionVersion
from app.models.session import Response, SessionQuestion, TestSession
from app.models.settings import PlatformSettings
from app.models.user import User

__all__ = [
    "AuditLog",
    "AuditOutcome",
    "Base",
    "CorrectOption",
    "ErasureJob",
    "ErasureJobStatus",
    "PlatformSettings",
    "Question",
    "QuestionVersion",
    "Response",
    "SelectedOption",
    "SelectionMode",
    "SessionQuestion",
    "SessionStatus",
    "TestSession",
    "User",
    "UserRole",
]
