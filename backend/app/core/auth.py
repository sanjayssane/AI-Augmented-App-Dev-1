"""Authentication request/session helpers and dependencies."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_csrf_service, get_db, get_session_store, get_user_repository
from app.models.enums import UserRole
from app.repositories.redis.session_store import ServerSession, SessionStore
from app.repositories.user_repository import UserRepository
from app.schemas.errors import ForbiddenError, UnauthenticatedError
from app.services.csrf_service import CsrfService


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


def require_csrf(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    csrf_service: Annotated[CsrfService, Depends(get_csrf_service)],
    x_csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> CurrentUser:
    csrf_service.validate_token(x_csrf_token, expected_token=current_user.csrf_token)
    return current_user


def require_admin_examiner(
    examiner: Annotated[CurrentUser, Depends(require_examiner)],
    db: Annotated[Session, Depends(get_db)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> CurrentUser:
    user = user_repo.find_by_id(db, examiner.user_id)
    if user is None or not user.is_admin:
        raise ForbiddenError()
    return examiner


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
ExaminerUserDep = Annotated[CurrentUser, Depends(require_examiner)]
ExamineeUserDep = Annotated[CurrentUser, Depends(require_examinee)]
CsrfProtectedDep = Annotated[CurrentUser, Depends(require_csrf)]
AdminExaminerDep = Annotated[CurrentUser, Depends(require_admin_examiner)]
