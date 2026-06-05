"""Examiner API schemas for questions, sessions, settings, and user admin."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.domain.validation import validate_password
from app.models.enums import CorrectOption, SelectedOption, SelectionMode, SessionStatus


class QuestionBase(BaseModel):
    question_text: str = Field(min_length=1, max_length=2000)
    option_a: str = Field(min_length=1, max_length=500)
    option_b: str = Field(min_length=1, max_length=500)
    option_c: str = Field(min_length=1, max_length=500)
    option_d: str = Field(min_length=1, max_length=500)
    correct_option: CorrectOption


class QuestionCreateRequest(QuestionBase):
    pass


class QuestionPatchRequest(BaseModel):
    question_text: str | None = Field(default=None, min_length=1, max_length=2000)
    option_a: str | None = Field(default=None, min_length=1, max_length=500)
    option_b: str | None = Field(default=None, min_length=1, max_length=500)
    option_c: str | None = Field(default=None, min_length=1, max_length=500)
    option_d: str | None = Field(default=None, min_length=1, max_length=500)
    correct_option: CorrectOption | None = None


class QuestionOut(QuestionBase):
    question_id: uuid.UUID
    question_version: int
    is_deleted: bool
    updated_at: datetime


class QuestionListData(BaseModel):
    items: list[QuestionOut]
    next_cursor: uuid.UUID | None
    active_count: int


class SessionSummaryOut(BaseModel):
    session_id: uuid.UUID
    status: SessionStatus
    score: int | None
    submitted_at: datetime | None
    prn: str | None
    name: str | None


class SessionListData(BaseModel):
    items: list[SessionSummaryOut]
    next_cursor: uuid.UUID | None


class SessionQuestionResultOut(BaseModel):
    question_id: uuid.UUID
    position: int
    question_text: str
    selected_option: SelectedOption | None
    correct_option: CorrectOption
    is_correct: bool | None


class SessionDetailOut(BaseModel):
    session_id: uuid.UUID
    status: SessionStatus
    score: int | None
    started_at: datetime
    submitted_at: datetime | None
    selection_mode: SelectionMode
    prn: str | None
    name: str | None
    responses: list[SessionQuestionResultOut]


class PlatformSettingsOut(BaseModel):
    retention_days_completed: int = Field(ge=1, le=3650)
    allow_examinee_retake: bool
    question_selection_mode: SelectionMode


class PlatformSettingsPatchRequest(BaseModel):
    retention_days_completed: int | None = Field(default=None, ge=1, le=3650)
    allow_examinee_retake: bool | None = None
    question_selection_mode: SelectionMode | None = None


class CreateExaminerRequest(BaseModel):
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=12, max_length=128)
    force_password_change: bool = True

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip()

    @field_validator("password")
    @classmethod
    def enforce_password_policy(cls, value: str) -> str:
        message = validate_password(value)
        if message:
            raise ValueError(message)
        return value


class ExaminerUserOut(BaseModel):
    user_id: uuid.UUID
    username: str
    is_active: bool
    force_password_change: bool
    created_at: datetime


class EraseExamineeResponse(BaseModel):
    user_id: uuid.UUID
    status: str = "accepted"
