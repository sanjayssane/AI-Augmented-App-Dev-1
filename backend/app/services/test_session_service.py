"""Examinee session retrieval and response autosave flows."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.concurrency import is_stale
from app.models.enums import CorrectOption, SelectedOption, SessionStatus
from app.models.question import Question
from app.models.session import Response, SessionQuestion
from app.repositories.response_repository import ResponseRepository
from app.repositories.test_session_repository import TestSessionRepository
from app.schemas.errors import ConflictError, ForbiddenError, NotFoundError, SessionNotFoundError


@dataclass
class SessionView:
    session_id: uuid.UUID
    status: SessionStatus
    answered_count: int
    current_position: int
    started_at: datetime
    expires_at: datetime


@dataclass
class QuestionAtPositionView:
    position: int
    total: int
    question_id: uuid.UUID
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    selected_option: SelectedOption | None
    answered_count: int


@dataclass
class SaveResponseView:
    question_id: uuid.UUID
    selected_option: SelectedOption | None
    updated_at: datetime
    answered_count: int


@dataclass
class ReviewItemView:
    position: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    selected_option: SelectedOption | None
    correct_option: CorrectOption
    is_correct: bool | None


class TestSessionService:
    def __init__(
        self,
        db: Session,
        test_session_repo: TestSessionRepository,
        response_repo: ResponseRepository,
    ) -> None:
        self._db = db
        self._test_session_repo = test_session_repo
        self._response_repo = response_repo

    def get_current_session(self, *, user_id: uuid.UUID) -> SessionView:
        current = self._test_session_repo.find_active_for_user(self._db, user_id)
        if current is None:
            current = self._test_session_repo.find_latest_for_user(self._db, user_id)
        if current is None:
            raise SessionNotFoundError()
        answered_count = self._response_repo.count_answered(self._db, session_id=current.session_id)
        return SessionView(
            session_id=current.session_id,
            status=current.status,
            answered_count=answered_count,
            current_position=1,
            started_at=current.start_time,
            expires_at=current.expires_at,
        )

    def get_question_at_position(
        self,
        *,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        position: int,
    ) -> QuestionAtPositionView:
        session = self._assert_owned_session(user_id=user_id, session_id=session_id)
        if session.status != SessionStatus.ACTIVE:
            raise ForbiddenError("Session is not active.")

        stmt = (
            select(SessionQuestion, Question, Response)
            .join(Question, Question.question_id == SessionQuestion.question_id)
            .join(
                Response,
                (Response.session_id == SessionQuestion.session_id)
                & (Response.question_id == SessionQuestion.question_id),
            )
            .where(
                SessionQuestion.session_id == session.session_id,
                SessionQuestion.position == position,
            )
        )
        row = self._db.execute(stmt).one_or_none()
        if row is None:
            raise NotFoundError("Question position was not found for this session.")

        session_question, question, response = row
        answered_count = self._response_repo.count_answered(self._db, session_id=session.session_id)
        return QuestionAtPositionView(
            position=session_question.position,
            total=50,
            question_id=question.question_id,
            question_text=question.question_text,
            option_a=question.option_a,
            option_b=question.option_b,
            option_c=question.option_c,
            option_d=question.option_d,
            selected_option=response.selected_option,
            answered_count=answered_count,
        )

    def save_response(
        self,
        *,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        question_id: uuid.UUID,
        selected_option: SelectedOption | None,
        if_unmodified_since: datetime | None,
    ) -> SaveResponseView:
        session = self._assert_owned_session(user_id=user_id, session_id=session_id)
        if session.status != SessionStatus.ACTIVE:
            raise ForbiddenError("Session is not active.")

        stmt = select(Response).where(
            Response.session_id == session.session_id,
            Response.question_id == question_id,
        )
        response = self._db.scalar(stmt)
        if response is None:
            raise NotFoundError("Response row was not found for this question.")

        if is_stale(if_unmodified_since, response.updated_at):
            raise ConflictError("Response was modified by another request.")

        response.selected_option = selected_option
        response.answered_at = datetime.now(response.updated_at.tzinfo)
        self._db.flush()
        answered_count = self._response_repo.count_answered(self._db, session_id=session.session_id)
        self._db.commit()
        self._db.refresh(response)

        return SaveResponseView(
            question_id=response.question_id,
            selected_option=response.selected_option,
            updated_at=response.updated_at,
            answered_count=answered_count,
        )

    def get_review(self, *, user_id: uuid.UUID, session_id: uuid.UUID) -> list[ReviewItemView]:
        session = self._assert_owned_session(user_id=user_id, session_id=session_id)
        if session.status != SessionStatus.COMPLETED:
            raise ForbiddenError("Review is available only after completion.")

        stmt = (
            select(SessionQuestion, Question, Response)
            .join(Question, Question.question_id == SessionQuestion.question_id)
            .join(
                Response,
                (Response.session_id == SessionQuestion.session_id)
                & (Response.question_id == SessionQuestion.question_id),
            )
            .where(SessionQuestion.session_id == session.session_id)
            .order_by(SessionQuestion.position.asc())
        )
        items: list[ReviewItemView] = []
        for session_question, question, response in self._db.execute(stmt).all():
            items.append(
                ReviewItemView(
                    position=session_question.position,
                    question_text=question.question_text,
                    option_a=question.option_a,
                    option_b=question.option_b,
                    option_c=question.option_c,
                    option_d=question.option_d,
                    selected_option=response.selected_option,
                    correct_option=question.correct_option,
                    is_correct=response.is_correct,
                )
            )
        return items

    def _assert_owned_session(self, *, user_id: uuid.UUID, session_id: uuid.UUID):
        session = self._test_session_repo.find_by_id(self._db, session_id)
        if session is None:
            raise SessionNotFoundError()
        if session.user_id != user_id:
            raise ForbiddenError("You do not own this session.")
        return session
