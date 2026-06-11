"""Authentication request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.encryption import normalise_prn
from app.domain.validation import validate_name, validate_prn
from app.models.enums import SessionStatus, UserRole


class ExaminerLoginRequest(BaseModel):
    """Credentials for examiner login."""

    username: str = Field(
        min_length=1,
        max_length=255,
        description="Examiner username (leading/trailing whitespace is trimmed).",
        examples=["examiner1"],
    )
    password: str = Field(
        min_length=1,
        max_length=128,
        description="Examiner password.",
        examples=["correct horse battery staple"],
    )

    @field_validator("username")
    @classmethod
    def strip_username(cls, value: str) -> str:
        return value.strip()


class ExaminerLoginResponse(BaseModel):
    """Examiner profile returned after a successful login."""

    user_id: uuid.UUID = Field(description="Unique identifier of the examiner.")
    username: str = Field(description="Examiner username.", examples=["examiner1"])
    must_change_password: bool = Field(
        default=False,
        description="True when the examiner must change their password before continuing.",
    )


class CsrfTokenResponse(BaseModel):
    """A CSRF token to send in the X-CSRF-Token header on mutating requests."""

    csrf_token: str = Field(
        description="Opaque CSRF token.",
        examples=["q1w2e3r4t5y6u7i8o9p0"],
    )


class ExamineeEntryRequest(BaseModel):
    """Examinee identification for registration or session resumption."""

    prn: str = Field(
        min_length=1,
        max_length=20,
        description="Permanent registration number (normalised to uppercase).",
        examples=["PRN2026001"],
    )
    name: str = Field(
        min_length=1,
        max_length=100,
        description="Examinee's full name as registered (whitespace trimmed).",
        examples=["Jane Doe"],
    )
    privacy_acknowledged: bool = Field(
        description="Must be true; confirms the examinee accepted the privacy notice.",
        examples=[True],
    )

    @field_validator("prn")
    @classmethod
    def validate_and_normalise_prn(cls, value: str) -> str:
        normalized = normalise_prn(value)
        error = validate_prn(normalized)
        if error is not None:
            raise ValueError(error)
        return normalized

    @field_validator("name")
    @classmethod
    def validate_and_trim_name(cls, value: str) -> str:
        trimmed, error = validate_name(value)
        if error is not None:
            raise ValueError(error)
        return trimmed

    @field_validator("privacy_acknowledged")
    @classmethod
    def require_privacy_acknowledgement(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Privacy acknowledgement is required.")
        return value


class ExamineeSessionResource(BaseModel):
    """Summary of an examinee's test session."""

    session_id: uuid.UUID = Field(description="Unique identifier of the test session.")
    status: SessionStatus = Field(description="Current session status.")
    total_questions: int = Field(default=50, description="Number of questions in the test.")
    answered_count: int = Field(description="Number of questions answered so far.")
    current_position: int = Field(
        default=1, description="Position (1-based) of the question the examinee is on."
    )
    started_at: datetime = Field(description="When the session was started (UTC).")
    expires_at: datetime = Field(description="When the session expires (UTC).")


class ExamineeEntryResult(BaseModel):
    """Internal service result pairing the session with a creation flag."""

    session: ExamineeSessionResource
    created: bool = Field(description="True when a new examinee account and session were created.")


class CurrentUserResponse(BaseModel):
    """Profile of the authenticated user; role-specific fields may be null."""

    user_id: uuid.UUID = Field(description="Unique identifier of the user.")
    role: UserRole = Field(description="Role of the authenticated user.")
    csrf_token: str = Field(
        description="Session-bound CSRF token to send in the X-CSRF-Token header on mutating requests."
    )
    prn: str | None = Field(
        default=None, description="Registration number (examinees only).", examples=["PRN2026001"]
    )
    name: str | None = Field(
        default=None, description="Full name (examinees only).", examples=["Jane Doe"]
    )
    username: str | None = Field(
        default=None, description="Username (examiners only).", examples=["examiner1"]
    )
    is_admin: bool = Field(
        default=False, description="True when the examiner has administrative privileges."
    )
