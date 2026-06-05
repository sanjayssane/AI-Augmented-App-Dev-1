"""Input validation rules (PRD §3.1, §3.1.6)."""

from __future__ import annotations

import re

PRN_PATTERN = re.compile(r"^[A-Za-z0-9]{1,20}$")
PASSWORD_MIN_LEN = 12
PASSWORD_MAX_LEN = 128


def validate_prn(prn: str) -> str | None:
    if not PRN_PATTERN.match(prn):
        return "PRN must contain only letters and numbers, up to 20 characters."
    return None


def validate_name(name: str) -> tuple[str, str | None]:
    trimmed = name.strip()
    if not trimmed:
        return trimmed, "Name is required."
    if len(trimmed) > 100:
        return trimmed, "Name must be at most 100 characters."
    return trimmed, None


def validate_password(password: str) -> str | None:
    if len(password) < PASSWORD_MIN_LEN:
        return f"Password must be at least {PASSWORD_MIN_LEN} characters."
    if len(password) > PASSWORD_MAX_LEN:
        return f"Password must be at most {PASSWORD_MAX_LEN} characters."
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return "Password must contain at least one digit."
    return None


def names_match(stored_name: str, provided_name: str) -> bool:
    return stored_name.strip().casefold() == provided_name.strip().casefold()
