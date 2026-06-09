"""Authentication request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.encryption import normalise_prn
from app.domain.validation import validate_name, validate_prn
from app.models.enums import SessionStatus, UserRole


class ExaminerLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("username")
    @classmethod
    def strip_username(cls, value: str) -> str:
        return value.strip()


class ExaminerLoginResponse(BaseModel):
    user_id: uuid.UUID
    username: str
    must_change_password: bool = False


class CsrfTokenResponse(BaseModel):
    csrf_token: str


class ExamineeEntryRequest(BaseModel):
    prn: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=100)
    privacy_acknowledged: bool

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
    session_id: uuid.UUID
    status: SessionStatus
    total_questions: int = 50
    answered_count: int
    current_position: int = 1
    started_at: datetime
    expires_at: datetime


class ExamineeEntryResult(BaseModel):
    session: ExamineeSessionResource
    created: bool


class CurrentUserResponse(BaseModel):
    user_id: uuid.UUID
    role: UserRole
    prn: str | None = None
    name: str | None = None
    username: str | None = None
    is_admin: bool = False
