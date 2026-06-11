"""Examiner API schemas for questions, sessions, settings, and user admin."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.domain.validation import validate_password
from app.models.enums import CorrectOption, SelectedOption, SelectionMode, SessionStatus


class QuestionBase(BaseModel):
    """Common fields of a multiple-choice question (examiner view)."""

    question_text: str = Field(
        min_length=1,
        max_length=2000,
        description="The question text.",
        examples=["What is the capital of France?"],
    )
    option_a: str = Field(min_length=1, max_length=500, description="Text of option A.", examples=["Paris"])
    option_b: str = Field(min_length=1, max_length=500, description="Text of option B.", examples=["London"])
    option_c: str = Field(min_length=1, max_length=500, description="Text of option C.", examples=["Berlin"])
    option_d: str = Field(min_length=1, max_length=500, description="Text of option D.", examples=["Madrid"])
    correct_option: CorrectOption = Field(description="Key of the correct option (A-D).", examples=["A"])


class QuestionCreateRequest(QuestionBase):
    """Payload to add a new question to the bank."""


class QuestionPatchRequest(BaseModel):
    """Partial question update; omitted fields keep their current values."""

    question_text: str | None = Field(
        default=None, min_length=1, max_length=2000, description="New question text."
    )
    option_a: str | None = Field(default=None, min_length=1, max_length=500, description="New text for option A.")
    option_b: str | None = Field(default=None, min_length=1, max_length=500, description="New text for option B.")
    option_c: str | None = Field(default=None, min_length=1, max_length=500, description="New text for option C.")
    option_d: str | None = Field(default=None, min_length=1, max_length=500, description="New text for option D.")
    correct_option: CorrectOption | None = Field(
        default=None, description="New key of the correct option (A-D)."
    )


class QuestionOut(QuestionBase):
    """A question bank entry, including the correct answer."""

    question_id: uuid.UUID = Field(description="Unique identifier of the question.")
    question_version: int = Field(
        description="Version number, incremented on every edit.", examples=[1]
    )
    is_deleted: bool = Field(description="True when the question has been soft-deleted.")
    updated_at: datetime = Field(description="When the question was last modified (UTC).")


class QuestionListData(BaseModel):
    """One page of the question bank."""

    items: list[QuestionOut] = Field(description="Questions in this page.")
    next_cursor: uuid.UUID | None = Field(
        description="Cursor for the next page; null when there are no more results."
    )
    active_count: int = Field(
        description="Total number of active (non-deleted) questions in the bank.", examples=[120]
    )


class SessionSummaryOut(BaseModel):
    """Summary row of an examinee test session."""

    session_id: uuid.UUID = Field(description="Unique identifier of the session.")
    status: SessionStatus = Field(description="Current session status.")
    score: int | None = Field(description="Final score; null until submitted.", examples=[42])
    submitted_at: datetime | None = Field(description="Submission time (UTC); null until submitted.")
    prn: str | None = Field(description="Examinee registration number.", examples=["PRN2026001"])
    name: str | None = Field(description="Examinee full name.", examples=["Jane Doe"])


class SessionListData(BaseModel):
    """One page of test session summaries."""

    items: list[SessionSummaryOut] = Field(description="Session summaries in this page.")
    next_cursor: uuid.UUID | None = Field(
        description="Cursor for the next page; null when there are no more results."
    )


class SessionQuestionResultOut(BaseModel):
    """Per-question result within a session detail."""

    question_id: uuid.UUID = Field(description="Unique identifier of the question.")
    position: int = Field(description="Position (1-based) of the question in the test.")
    question_text: str = Field(description="The question text.")
    selected_option: SelectedOption | None = Field(
        description="The examinee's selected option (null if unanswered)."
    )
    correct_option: CorrectOption = Field(description="The correct option key.")
    is_correct: bool | None = Field(
        description="Whether the answer was correct (null if unanswered)."
    )


class SessionDetailOut(BaseModel):
    """Full detail of a test session including per-question results."""

    session_id: uuid.UUID = Field(description="Unique identifier of the session.")
    user_id: uuid.UUID = Field(description="Unique identifier of the examinee.")
    status: SessionStatus = Field(description="Current session status.")
    score: int | None = Field(description="Final score; null until submitted.")
    started_at: datetime = Field(description="When the session was started (UTC).")
    submitted_at: datetime | None = Field(description="Submission time (UTC); null until submitted.")
    selection_mode: SelectionMode = Field(
        description="How questions were selected for this session."
    )
    prn: str | None = Field(description="Examinee registration number.")
    name: str | None = Field(description="Examinee full name.")
    responses: list[SessionQuestionResultOut] = Field(
        description="Per-question results in test order."
    )


class PlatformSettingsOut(BaseModel):
    """Current platform settings."""

    retention_days_completed: int = Field(
        ge=1,
        le=3650,
        description="Days completed sessions are retained before automatic deletion.",
        examples=[365],
    )
    allow_examinee_retake: bool = Field(
        description="Whether examinees who completed the test may take it again."
    )
    question_selection_mode: SelectionMode = Field(
        description="How questions are selected when a new test session starts."
    )


class PlatformSettingsPatchRequest(BaseModel):
    """Partial settings update; omitted fields are left unchanged."""

    retention_days_completed: int | None = Field(
        default=None,
        ge=1,
        le=3650,
        description="New retention period in days (1-3650).",
    )
    allow_examinee_retake: bool | None = Field(
        default=None, description="New retake policy."
    )
    question_selection_mode: SelectionMode | None = Field(
        default=None, description="New question selection mode."
    )


class CreateExaminerRequest(BaseModel):
    """Payload to create a new examiner account (admin only)."""

    username: str = Field(
        min_length=1,
        max_length=255,
        description="Username for the new examiner (whitespace trimmed).",
        examples=["examiner2"],
    )
    password: str = Field(
        min_length=12,
        max_length=128,
        description="Initial password; must satisfy the platform password policy (minimum 12 characters).",
    )
    force_password_change: bool = Field(
        default=True,
        description="When true, the examiner must change the password on first login.",
    )

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
    """A created examiner account."""

    user_id: uuid.UUID = Field(description="Unique identifier of the examiner.")
    username: str = Field(description="Examiner username.", examples=["examiner2"])
    is_active: bool = Field(description="Whether the account is active.")
    force_password_change: bool = Field(
        description="Whether the examiner must change their password on first login."
    )
    created_at: datetime = Field(description="When the account was created (UTC).")


class EraseExamineeResponse(BaseModel):
    """Acknowledgement of an accepted GDPR erasure request."""

    user_id: uuid.UUID = Field(description="The examinee whose data will be erased.")
    job_id: uuid.UUID = Field(description="Identifier of the asynchronous erasure job.")
    status: str = Field(
        default="accepted", description="Job status at acceptance time.", examples=["accepted"]
    )
