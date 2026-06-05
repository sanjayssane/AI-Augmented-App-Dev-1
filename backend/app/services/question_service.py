"""Examiner question bank use cases."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import CorrectOption
from app.models.question import Question
from app.repositories.question_repository import QuestionRepository
from app.repositories.question_version_repository import QuestionVersionRepository
from app.schemas.errors import BankBelowMinimumError, NotFoundError


@dataclass
class QuestionPayload:
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: CorrectOption


class QuestionService:
    def __init__(
        self,
        db: Session,
        question_repo: QuestionRepository,
        question_version_repo: QuestionVersionRepository,
    ) -> None:
        self._db = db
        self._question_repo = question_repo
        self._question_version_repo = question_version_repo

    def list_questions(
        self,
        *,
        limit: int = 50,
        cursor: uuid.UUID | None = None,
        include_deleted: bool = False,
    ) -> tuple[list, uuid.UUID | None, int]:
        rows = self._question_repo.list(
            self._db,
            limit=limit,
            cursor=cursor,
            include_deleted=include_deleted,
        )
        next_cursor = rows[-1].question_id if len(rows) == limit else None
        active_count = self._question_repo.count_active(self._db)
        return rows, next_cursor, active_count

    def get_question(self, *, question_id: uuid.UUID):
        question = self._db.get(Question, question_id)
        if question is None:
            raise NotFoundError("Question not found.")
        return question

    def create_question(self, *, payload: QuestionPayload, created_by: uuid.UUID):
        question = self._question_repo.create(
            self._db,
            question_text=payload.question_text,
            option_a=payload.option_a,
            option_b=payload.option_b,
            option_c=payload.option_c,
            option_d=payload.option_d,
            correct_option=payload.correct_option,
            created_by=created_by,
        )
        self._db.commit()
        self._db.refresh(question)
        return question

    def patch_question(
        self,
        *,
        question_id: uuid.UUID,
        actor_id: uuid.UUID,
        payload: QuestionPayload,
    ):
        question = self.get_question(question_id=question_id)

        self._question_version_repo.archive(
            self._db,
            question=question,
            modified_by=actor_id,
        )
        updated = self._question_repo.update(
            self._db,
            question,
            question_text=payload.question_text,
            option_a=payload.option_a,
            option_b=payload.option_b,
            option_c=payload.option_c,
            option_d=payload.option_d,
            correct_option=payload.correct_option,
        )
        self._db.commit()
        self._db.refresh(updated)
        return updated

    def delete_question(self, *, question_id: uuid.UUID):
        question = self.get_question(question_id=question_id)
        if question.is_deleted:
            return question

        active_count = self._question_repo.count_active(self._db)
        if active_count - 1 < settings.min_active_questions:
            raise BankBelowMinimumError(active_count=active_count - 1)

        deleted = self._question_repo.soft_delete(self._db, question)
        self._db.commit()
        self._db.refresh(deleted)
        return deleted
