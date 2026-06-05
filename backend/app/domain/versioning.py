"""Question versioning rules (PRD §3.5.3–3.5.4)."""

from __future__ import annotations

MIN_ACTIVE_QUESTIONS = 50


def can_soft_delete(active_count: int) -> bool:
    return active_count - 1 >= MIN_ACTIVE_QUESTIONS
