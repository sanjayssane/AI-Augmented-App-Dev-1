"""QuestionVersion data access."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.question import Question, QuestionVersion


class QuestionVersionRepository:
    def archive(
        self,
        session: Session,
        *,
        question: Question,
        modified_by: uuid.UUID,
    ) -> QuestionVersion:
        version = QuestionVersion(
            question_id=question.question_id,
            version_number=question.question_version,
            question_text=question.question_text,
            option_a=question.option_a,
            option_b=question.option_b,
            option_c=question.option_c,
            option_d=question.option_d,
            correct_option=question.correct_option,
            modified_by=modified_by,
        )
        session.add(version)
        session.flush()
        return version

    def get_by_question_and_version(
        self,
        session: Session,
        *,
        question_id: uuid.UUID,
        version_number: int,
    ) -> QuestionVersion | None:
        stmt = select(QuestionVersion).where(
            QuestionVersion.question_id == question_id,
            QuestionVersion.version_number == version_number,
        )
        return session.scalar(stmt)
