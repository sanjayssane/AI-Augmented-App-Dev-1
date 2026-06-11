"""Examinee test flow request/response schemas (PRD §9.6.4)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.enums import CorrectOption, SelectedOption, SessionStatus


class QuestionOption(BaseModel):
    """One of the four answer options for a question."""

    key: CorrectOption = Field(description="Option key (A, B, C, or D).")
    text: str = Field(description="Option text.", examples=["Paris"])


class SessionQuestionPayload(BaseModel):
    """A question as presented to the examinee (the correct answer is never included)."""

    question_id: uuid.UUID = Field(description="Unique identifier of the question.")
    question_text: str = Field(
        description="The question text.", examples=["What is the capital of France?"]
    )
    options: list[QuestionOption] = Field(description="The four answer options (A-D).")


class ExamineeSessionResource(BaseModel):
    """Summary of an examinee's test session."""

    session_id: uuid.UUID = Field(description="Unique identifier of the test session.")
    status: SessionStatus = Field(description="Current session status.")
    total_questions: int = Field(default=50, description="Number of questions in the test.")
    answered_count: int = Field(default=0, description="Number of questions answered so far.")
    current_position: int = Field(
        default=1, description="Position (1-based) of the question the examinee is on."
    )
    started_at: datetime = Field(description="When the session was started (UTC).")
    expires_at: datetime = Field(description="When the session expires (UTC).")


class ExamineeQuestionAtPositionResource(BaseModel):
    """A question at a given position, with the examinee's current selection."""

    position: int = Field(ge=1, le=50, description="Position (1-based) of this question.")
    total: int = Field(default=50, description="Total number of questions in the test.")
    question: SessionQuestionPayload = Field(description="The question and its options.")
    selected_option: SelectedOption | None = Field(
        default=None, description="The examinee's previously selected option, if any."
    )
    answered_count: int = Field(description="Number of questions answered so far.")


class SaveResponseRequest(BaseModel):
    """Answer selection for a question; null clears the answer."""

    selected_option: SelectedOption | None = Field(
        default=None,
        description="Selected option key (A-D), or null to clear the answer.",
        examples=["B"],
    )


class SaveResponseResult(BaseModel):
    """Confirmation of a saved answer."""

    question_id: uuid.UUID = Field(description="The question the response belongs to.")
    selected_option: SelectedOption | None = Field(
        default=None, description="The stored option after the save (null when cleared)."
    )
    updated_at: datetime = Field(
        description="Server timestamp of the save; usable in subsequent If-Unmodified-Since headers."
    )
    answered_count: int = Field(description="Number of questions answered after this save.")


class SubmitSessionRequest(BaseModel):
    """Explicit confirmation required to submit the test."""

    confirm: Literal[True] = Field(
        description="Must be true; guards against accidental submission.", examples=[True]
    )


class SubmitSessionResult(BaseModel):
    """Final score breakdown after submission."""

    session_id: uuid.UUID = Field(description="Unique identifier of the submitted session.")
    status: SessionStatus = Field(description="Session status after submission.")
    score: int = Field(description="Number of correct answers.", examples=[42])
    max_score: int = Field(default=50, description="Maximum achievable score.")
    correct_count: int = Field(description="Number of correctly answered questions.")
    incorrect_count: int = Field(description="Number of incorrectly answered questions.")
    unattempted_count: int = Field(description="Number of unanswered questions.")
    submitted_at: datetime = Field(description="When the session was submitted (UTC).")


class ReviewItem(BaseModel):
    """Per-question review entry, available after submission."""

    position: int = Field(ge=1, le=50, description="Position (1-based) of the question.")
    question_text: str = Field(description="The question text.")
    options: list[QuestionOption] = Field(description="The four answer options (A-D).")
    selected_option: SelectedOption | None = Field(
        default=None, description="The examinee's selected option (null if unanswered)."
    )
    correct_option: CorrectOption = Field(description="The correct option key.")
    is_correct: bool | None = Field(
        default=None, description="Whether the answer was correct (null if unanswered)."
    )


class ReviewResult(BaseModel):
    """Full post-submission review of all questions."""

    items: list[ReviewItem] = Field(description="Review entries in question order.")
