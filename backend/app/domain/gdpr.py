"""GDPR anonymisation helpers (PRD §5.5)."""

from __future__ import annotations

import uuid


def erasure_token() -> str:
    return f"ERASED-{uuid.uuid4()}"
