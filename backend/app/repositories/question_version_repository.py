"""QuestionVersion data access."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import CorrectOption
from app.models.question import Question, QuestionVersion


@dataclass(frozen=True)
class ScoringQuestionVersion:
    correct_option: CorrectOption


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

    def resolve_for_scoring(
        self,
        session: Session,
        *,
        question_id: uuid.UUID,
        version_number: int,
    ) -> ScoringQuestionVersion | None:
        """Resolve frozen snapshot for scoring.

        Archived rows hold superseded versions; the live question row holds the
        current version until the next edit archives it.
        """
        archived = self.get_by_question_and_version(
            session,
            question_id=question_id,
            version_number=version_number,
        )
        if archived is not None:
            return ScoringQuestionVersion(correct_option=archived.correct_option)

        question = session.get(Question, question_id)
        if question is None or question.question_version != version_number:
            return None
        return ScoringQuestionVersion(correct_option=question.correct_option)
