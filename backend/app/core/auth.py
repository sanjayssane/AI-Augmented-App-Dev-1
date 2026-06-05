"""Authentication request/session helpers and dependencies."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request

from app.core.config import settings
from app.core.deps import get_session_store
from app.models.enums import UserRole
from app.repositories.redis.session_store import ServerSession, SessionStore
from app.schemas.errors import ForbiddenError, UnauthenticatedError


@dataclass(frozen=True)
class CurrentUser:
    user_id: uuid.UUID
    role: UserRole
    session_token: str
    csrf_token: str


def get_session_from_request(
    request: Request,
    session_store: Annotated[SessionStore, Depends(get_session_store)],
) -> ServerSession | None:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return None
    session = session_store.get_session(token)
    if session is None:
        return None
    session_store.touch_session(token)
    return session


def get_current_user(
    server_session: Annotated[ServerSession | None, Depends(get_session_from_request)],
) -> CurrentUser:
    if server_session is None:
        raise UnauthenticatedError()
    return CurrentUser(
        user_id=server_session.user_id,
        role=server_session.role,
        session_token=server_session.session_token,
        csrf_token=server_session.csrf_token,
    )


def require_examiner(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    if current_user.role != UserRole.EXAMINER:
        raise ForbiddenError()
    return current_user


def require_examinee(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    if current_user.role != UserRole.EXAMINEE:
        raise ForbiddenError()
    return current_user


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
ExaminerUserDep = Annotated[CurrentUser, Depends(require_examiner)]
ExamineeUserDep = Annotated[CurrentUser, Depends(require_examinee)]
