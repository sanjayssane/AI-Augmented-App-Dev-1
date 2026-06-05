"""Question selection for new test sessions (PRD §3.6.1)."""

from __future__ import annotations

import random
import uuid

from app.models.enums import SelectionMode
from app.models.question import Question

MIN_BANK_SIZE = 50
SESSION_QUESTION_COUNT = 50


def select_questions(
    questions: list[Question],
    mode: SelectionMode,
) -> list[tuple[uuid.UUID, int]]:
    """Return (question_id, version_snapshot) pairs in display order."""
    if len(questions) < MIN_BANK_SIZE:
        msg = f"At least {MIN_BANK_SIZE} active questions required."
        raise ValueError(msg)

    pool = list(questions)
    if mode == SelectionMode.RANDOM_SAMPLE:
        random.shuffle(pool)
    selected = pool[:SESSION_QUESTION_COUNT]
    return [(q.question_id, q.question_version) for q in selected]
