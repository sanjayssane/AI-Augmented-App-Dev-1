"""Examinee test flow request/response schemas (PRD §9.6.4)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.enums import CorrectOption, SelectedOption, SessionStatus


class QuestionOption(BaseModel):
    key: CorrectOption
    text: str


class SessionQuestionPayload(BaseModel):
    question_id: uuid.UUID
    question_text: str
    options: list[QuestionOption]


class ExamineeSessionResource(BaseModel):
    session_id: uuid.UUID
    status: SessionStatus
    total_questions: int = 50
    answered_count: int = 0
    current_position: int = 1
    started_at: datetime
    expires_at: datetime


class ExamineeQuestionAtPositionResource(BaseModel):
    position: int = Field(ge=1, le=50)
    total: int = 50
    question: SessionQuestionPayload
    selected_option: SelectedOption | None = None
    answered_count: int


class SaveResponseRequest(BaseModel):
    selected_option: SelectedOption | None = None


class SaveResponseResult(BaseModel):
    question_id: uuid.UUID
    selected_option: SelectedOption | None = None
    updated_at: datetime
    answered_count: int


class SubmitSessionRequest(BaseModel):
    confirm: Literal[True]


class SubmitSessionResult(BaseModel):
    session_id: uuid.UUID
    status: SessionStatus
    score: int
    max_score: int = 50
    correct_count: int
    incorrect_count: int
    unattempted_count: int
    submitted_at: datetime


class ReviewItem(BaseModel):
    position: int = Field(ge=1, le=50)
    question_text: str
    options: list[QuestionOption]
    selected_option: SelectedOption | None = None
    correct_option: CorrectOption
    is_correct: bool | None = None


class ReviewResult(BaseModel):
    items: list[ReviewItem]
