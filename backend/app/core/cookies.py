"""HttpOnly session cookie helpers."""

from __future__ import annotations

from fastapi import Response

from app.core.config import settings


def set_session_cookie(response: Response, token: str, *, max_age: int | None = None) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=max_age or settings.examiner_session_ttl_seconds,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="strict",
        path=settings.session_cookie_path,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.session_cookie_name,
        path=settings.session_cookie_path,
    )
