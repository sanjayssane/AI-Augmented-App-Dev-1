"""Submit and score examinee sessions server-side."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.scoring import compute_score, is_response_correct
from app.models.enums import SessionStatus
from app.models.session import Response, SessionQuestion
from app.repositories.question_version_repository import QuestionVersionRepository
from app.repositories.redis.submit_idempotency_store import SubmitIdempotencyStore
from app.repositories.response_repository import ResponseRepository
from app.repositories.test_session_repository import TestSessionRepository
from app.schemas.errors import ConflictError, ForbiddenError, NotFoundError


@dataclass
class SubmitSessionView:
    session_id: uuid.UUID
    status: SessionStatus
    score: int
    max_score: int
    correct_count: int
    incorrect_count: int
    unattempted_count: int
    submitted_at: datetime

    def to_idempotency_payload(self) -> dict:
        return {
            "session_id": str(self.session_id),
            "status": self.status.value,
            "score": self.score,
            "max_score": self.max_score,
            "correct_count": self.correct_count,
            "incorrect_count": self.incorrect_count,
            "unattempted_count": self.unattempted_count,
            "submitted_at": self.submitted_at.isoformat(),
        }

    @classmethod
    def from_idempotency_payload(cls, payload: dict) -> "SubmitSessionView":
        return cls(
            session_id=uuid.UUID(payload["session_id"]),
            status=SessionStatus(payload["status"]),
            score=int(payload["score"]),
            max_score=int(payload["max_score"]),
            correct_count=int(payload["correct_count"]),
            incorrect_count=int(payload["incorrect_count"]),
            unattempted_count=int(payload["unattempted_count"]),
            submitted_at=datetime.fromisoformat(payload["submitted_at"]),
        )


class ScoringService:
    def __init__(
        self,
        db: Session,
        test_session_repo: TestSessionRepository,
        response_repo: ResponseRepository,
        question_version_repo: QuestionVersionRepository,
        submit_idempotency_store: SubmitIdempotencyStore,
    ) -> None:
        self._db = db
        self._test_session_repo = test_session_repo
        self._response_repo = response_repo
        self._question_version_repo = question_version_repo
        self._submit_idempotency_store = submit_idempotency_store

    def submit_session(
        self,
        *,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        idempotency_key: str | None,
    ) -> SubmitSessionView:
        if idempotency_key:
            cached = self._submit_idempotency_store.get(idempotency_key)
            if cached is not None:
                return SubmitSessionView.from_idempotency_payload(cached)

        session = self._test_session_repo.find_by_id(self._db, session_id)
        if session is None:
            raise NotFoundError("Session was not found.")
        if session.user_id != user_id:
            raise ForbiddenError("You do not own this session.")
        if session.status != SessionStatus.ACTIVE:
            raise ConflictError("Session is already submitted or expired.")

        stmt = (
            select(SessionQuestion, Response)
            .join(
                Response,
                (Response.session_id == SessionQuestion.session_id)
                & (Response.question_id == SessionQuestion.question_id),
            )
            .where(SessionQuestion.session_id == session.session_id)
            .order_by(SessionQuestion.position.asc())
        )
        rows = self._db.execute(stmt).all()
        if not rows:
            raise NotFoundError("Session questions were not found.")

        correctness: dict[uuid.UUID, bool] = {}
        results: list[bool | None] = []
        for session_question, response in rows:
            question_version = self._question_version_repo.resolve_for_scoring(
                self._db,
                question_id=session_question.question_id,
                version_number=session_question.question_version_snapshot,
            )
            if question_version is None:
                raise NotFoundError("Question version snapshot not found.")

            result = is_response_correct(
                response.selected_option,
                question_version.correct_option,
            )
            results.append(result)
            correctness[session_question.question_id] = bool(result) if result is not None else False

        self._response_repo.bulk_set_correctness(
            self._db,
            session_id=session.session_id,
            correctness_by_question_id=correctness,
        )
        score, correct_count, incorrect_count, unattempted_count = compute_score(results)
        completed_at = datetime.now(UTC)
        self._test_session_repo.complete(
            self._db,
            session,
            score=score,
            end_time=completed_at,
        )
        self._db.commit()

        view = SubmitSessionView(
            session_id=session.session_id,
            status=SessionStatus.COMPLETED,
            score=score,
            max_score=50,
            correct_count=correct_count,
            incorrect_count=incorrect_count,
            unattempted_count=unattempted_count,
            submitted_at=completed_at,
        )
        if idempotency_key:
            self._submit_idempotency_store.put(idempotency_key, view.to_idempotency_payload())
        return view
