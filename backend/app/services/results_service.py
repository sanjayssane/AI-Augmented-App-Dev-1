"""Examiner results listing/detail/export use cases."""

from __future__ import annotations

import csv
import io
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.encryption import decrypt_field
from app.models.question import Question
from app.models.session import Response, SessionQuestion, TestSession
from app.models.user import User
from app.repositories.test_session_repository import TestSessionRepository
from app.schemas.errors import NotFoundError


@dataclass
class SessionSummary:
    session_id: uuid.UUID
    status: object
    score: int | None
    submitted_at: object | None
    prn: str | None
    name: str | None


@dataclass
class SessionQuestionResult:
    question_id: uuid.UUID
    position: int
    question_text: str
    selected_option: object | None
    correct_option: object
    is_correct: bool | None


@dataclass
class SessionDetail:
    session_id: uuid.UUID
    status: object
    score: int | None
    started_at: object
    submitted_at: object | None
    selection_mode: object
    prn: str | None
    name: str | None
    responses: list[SessionQuestionResult]


class ResultsService:
    def __init__(self, db: Session, session_repo: TestSessionRepository) -> None:
        self._db = db
        self._session_repo = session_repo

    def list_sessions(
        self,
        *,
        limit: int = 50,
        cursor: uuid.UUID | None = None,
    ) -> tuple[list[SessionSummary], uuid.UUID | None]:
        sessions = self._session_repo.list_for_examiner(
            self._db,
            limit=limit,
            cursor=cursor,
        )
        summaries = [self._to_summary(row) for row in sessions]
        next_cursor = sessions[-1].session_id if len(sessions) == limit else None
        return summaries, next_cursor

    def get_session_detail(self, *, session_id: uuid.UUID) -> SessionDetail:
        session_row = self._session_repo.find_by_id(self._db, session_id)
        if session_row is None:
            raise NotFoundError("Session not found.")

        user = self._db.get(User, session_row.user_id)
        prn, name = self._decode_user_pii(user)

        stmt = (
            select(SessionQuestion, Response, Question)
            .join(
                Response,
                (Response.session_id == SessionQuestion.session_id)
                & (Response.question_id == SessionQuestion.question_id),
            )
            .join(Question, Question.question_id == SessionQuestion.question_id)
            .where(SessionQuestion.session_id == session_id)
            .order_by(SessionQuestion.position.asc())
        )
        rows = self._db.execute(stmt).all()

        responses = [
            SessionQuestionResult(
                question_id=question.question_id,
                position=session_question.position,
                question_text=question.question_text,
                selected_option=response.selected_option,
                correct_option=question.correct_option,
                is_correct=response.is_correct,
            )
            for session_question, response, question in rows
        ]

        return SessionDetail(
            session_id=session_row.session_id,
            status=session_row.status,
            score=session_row.score,
            started_at=session_row.start_time,
            submitted_at=session_row.end_time,
            selection_mode=session_row.selection_mode,
            prn=prn,
            name=name,
            responses=responses,
        )

    def get_session(self, *, session_id: uuid.UUID) -> SessionDetail:
        return self.get_session_detail(session_id=session_id)

    def export_sessions_csv(self, *, anonymised: bool = False) -> str:
        stmt = select(TestSession).order_by(TestSession.start_time.desc())
        sessions = list(self._db.scalars(stmt).all())

        output = io.StringIO()
        writer = csv.writer(output)
        if anonymised:
            writer.writerow(
                [
                    "session_id",
                    "score",
                    "submitted_at",
                    "status",
                ]
            )
        else:
            writer.writerow(
                [
                    "session_id",
                    "prn",
                    "name",
                    "score",
                    "submitted_at",
                    "status",
                ]
            )

        for row in sessions:
            user = self._db.get(User, row.user_id)
            prn, name = self._decode_user_pii(user)
            if anonymised:
                writer.writerow(
                    [
                        str(row.session_id),
                        row.score,
                        row.end_time.isoformat() if row.end_time else "",
                        row.status.value,
                    ]
                )
            else:
                writer.writerow(
                    [
                        str(row.session_id),
                        prn or "",
                        name or "",
                        row.score,
                        row.end_time.isoformat() if row.end_time else "",
                        row.status.value,
                    ]
                )

        return "\ufeff" + output.getvalue()

    def export_sessions(self, *, anonymised: bool = False) -> str:
        return self.export_sessions_csv(anonymised=anonymised)

    def _to_summary(self, row: TestSession) -> SessionSummary:
        user = self._db.get(User, row.user_id)
        prn, name = self._decode_user_pii(user)
        return SessionSummary(
            session_id=row.session_id,
            status=row.status.value,
            score=row.score,
            submitted_at=row.end_time,
            prn=prn,
            name=name,
        )

    @staticmethod
    def _decode_user_pii(user: User | None) -> tuple[str | None, str | None]:
        if user is None:
            return None, None
        if not user.prn_ciphertext or not user.name_ciphertext:
            return None, None
        return decrypt_field(user.prn_ciphertext), decrypt_field(user.name_ciphertext)
