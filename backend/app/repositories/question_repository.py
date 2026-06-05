"""Question data access."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import CorrectOption
from app.models.question import Question


class QuestionRepository:
    def list(
        self,
        session: Session,
        *,
        limit: int,
        cursor: uuid.UUID | None = None,
        include_deleted: bool = False,
    ) -> list[Question]:
        stmt = select(Question)
        if not include_deleted:
            stmt = stmt.where(Question.is_deleted.is_(False))
        if cursor is not None:
            stmt = stmt.where(Question.question_id > cursor)
        stmt = stmt.order_by(Question.question_id.asc()).limit(limit)
        return list(session.scalars(stmt).all())

    def create(
        self,
        session: Session,
        *,
        question_text: str,
        option_a: str,
        option_b: str,
        option_c: str,
        option_d: str,
        correct_option: CorrectOption,
        created_by: uuid.UUID,
    ) -> Question:
        question = Question(
            question_text=question_text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_option=correct_option,
            created_by=created_by,
            question_version=1,
            is_deleted=False,
        )
        session.add(question)
        session.flush()
        return question

    def update(
        self,
        session: Session,
        question: Question,
        *,
        question_text: str,
        option_a: str,
        option_b: str,
        option_c: str,
        option_d: str,
        correct_option: CorrectOption,
    ) -> Question:
        question.question_text = question_text
        question.option_a = option_a
        question.option_b = option_b
        question.option_c = option_c
        question.option_d = option_d
        question.correct_option = correct_option
        question.question_version += 1
        session.flush()
        return question

    def soft_delete(self, session: Session, question: Question) -> Question:
        question.is_deleted = True
        question.deleted_at = datetime.now(UTC)
        session.flush()
        return question

    def count_active(self, session: Session) -> int:
        stmt = select(func.count(Question.question_id)).where(Question.is_deleted.is_(False))
        return int(session.scalar(stmt) or 0)

    def list_active_for_selection(self, session: Session, *, limit: int) -> list[Question]:
        stmt = (
            select(Question)
            .where(Question.is_deleted.is_(False))
            .order_by(Question.question_id.asc())
            .limit(limit)
        )
        return list(session.scalars(stmt).all())
