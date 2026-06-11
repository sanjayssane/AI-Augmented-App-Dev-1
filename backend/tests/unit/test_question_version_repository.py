"""Unit tests for question version resolution during scoring."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from app.models.enums import CorrectOption
from app.models.question import Question, QuestionVersion
from app.repositories.question_version_repository import QuestionVersionRepository


@pytest.fixture
def repo() -> QuestionVersionRepository:
    return QuestionVersionRepository()


def test_resolve_for_scoring_uses_archived_version(repo: QuestionVersionRepository) -> None:
    db = MagicMock()
    question_id = uuid.uuid4()
    archived = QuestionVersion(
        question_id=question_id,
        version_number=1,
        question_text="Old text",
        option_a="A",
        option_b="B",
        option_c="C",
        option_d="D",
        correct_option=CorrectOption.B,
        modified_by=uuid.uuid4(),
    )
    db.scalar.return_value = archived

    resolved = repo.resolve_for_scoring(db, question_id=question_id, version_number=1)

    assert resolved is not None
    assert resolved.correct_option == CorrectOption.B
    db.get.assert_not_called()


def test_resolve_for_scoring_falls_back_to_live_question(repo: QuestionVersionRepository) -> None:
    db = MagicMock()
    question_id = uuid.uuid4()
    db.scalar.return_value = None
    db.get.return_value = Question(
        question_id=question_id,
        question_text="Current text",
        option_a="A",
        option_b="B",
        option_c="C",
        option_d="D",
        correct_option=CorrectOption.C,
        question_version=2,
        created_by=uuid.uuid4(),
        is_deleted=False,
    )

    resolved = repo.resolve_for_scoring(db, question_id=question_id, version_number=2)

    assert resolved is not None
    assert resolved.correct_option == CorrectOption.C


def test_resolve_for_scoring_returns_none_when_version_missing(repo: QuestionVersionRepository) -> None:
    db = MagicMock()
    question_id = uuid.uuid4()
    db.scalar.return_value = None
    db.get.return_value = Question(
        question_id=question_id,
        question_text="Current text",
        option_a="A",
        option_b="B",
        option_c="C",
        option_d="D",
        correct_option=CorrectOption.A,
        question_version=3,
        created_by=uuid.uuid4(),
        is_deleted=False,
    )

    resolved = repo.resolve_for_scoring(db, question_id=question_id, version_number=1)

    assert resolved is None
