"""Server-side scoring (PRD §3.3)."""

from __future__ import annotations

from app.models.enums import CorrectOption, SelectedOption


def is_response_correct(
    selected: SelectedOption | None,
    correct: CorrectOption,
) -> bool | None:
    if selected is None:
        return None
    return selected.value == correct.value


def compute_score(results: list[bool | None]) -> tuple[int, int, int, int]:
    """Return score, correct_count, incorrect_count, unattempted_count."""
    correct = sum(1 for r in results if r is True)
    incorrect = sum(1 for r in results if r is False)
    unattempted = sum(1 for r in results if r is None)
    return correct, correct, incorrect, unattempted
