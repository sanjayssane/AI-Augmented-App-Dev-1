"""Unit tests for AuthService.examiner_login."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from app.core.passwords import hash_password
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.redis.lockout_store import LockoutState
from app.schemas.errors import AccountLockedError, InvalidCredentialsError
from app.services.auth_service import AuthService


@pytest.fixture
def examiner_user() -> User:
    return User(
        user_id=uuid.uuid4(),
        username="examiner1",
        role=UserRole.EXAMINER,
        password_hash=hash_password("SecurePass123!"),
        is_active=True,
    )


@pytest.fixture
def auth_service() -> tuple[AuthService, dict[str, MagicMock]]:
    db = MagicMock()
    user_repo = MagicMock()
    session_store = MagicMock()
    lockout_store = MagicMock()
    audit_service = MagicMock()
    test_session_repo = MagicMock()
    question_repo = MagicMock()
    platform_settings_repo = MagicMock()
    rate_limit_store = MagicMock()
    response_repo = MagicMock()
    service = AuthService(
        db=db,
        user_repo=user_repo,
        session_store=session_store,
        lockout_store=lockout_store,
        audit_service=audit_service,
        test_session_repo=test_session_repo,
        question_repo=question_repo,
        platform_settings_repo=platform_settings_repo,
        rate_limit_store=rate_limit_store,
        response_repo=response_repo,
    )
    deps = {
        "db": db,
        "user_repo": user_repo,
        "session_store": session_store,
        "lockout_store": lockout_store,
        "audit_service": audit_service,
        "test_session_repo": test_session_repo,
        "question_repo": question_repo,
        "platform_settings_repo": platform_settings_repo,
        "rate_limit_store": rate_limit_store,
        "response_repo": response_repo,
    }
    return service, deps


def test_examiner_login_success(auth_service, examiner_user) -> None:
    service, deps = auth_service
    deps["lockout_store"].is_locked.return_value = None
    deps["user_repo"].find_examiner_by_username.return_value = examiner_user
    deps["session_store"].create_session.return_value = "session-token-abc"

    result = service.examiner_login(
        username="examiner1",
        password="SecurePass123!",
        client_ip="127.0.0.1",
    )

    assert result.user_id == examiner_user.user_id
    assert result.username == "examiner1"
    assert result.session_token == "session-token-abc"
    deps["lockout_store"].clear.assert_called_once_with("examiner1")
    deps["session_store"].invalidate_all_for_user.assert_called_once_with(examiner_user.user_id)
    deps["session_store"].create_session.assert_called_once_with(
        examiner_user.user_id,
        UserRole.EXAMINER,
    )
    deps["audit_service"].log_login_success.assert_called_once_with(
        examiner_user.user_id,
        "127.0.0.1",
    )


def test_examiner_login_wrong_password_raises_invalid_credentials(
    auth_service,
    examiner_user,
) -> None:
    service, deps = auth_service
    deps["lockout_store"].is_locked.return_value = None
    deps["user_repo"].find_examiner_by_username.return_value = examiner_user
    deps["lockout_store"].record_failure.return_value = LockoutState(
        failed_count=1,
        window_start=datetime.now(UTC),
        locked_until=None,
    )

    with pytest.raises(InvalidCredentialsError):
        service.examiner_login(
            username="examiner1",
            password="wrong-password",
            client_ip=None,
        )

    deps["audit_service"].log_login_failed.assert_called_once()


def test_examiner_login_unknown_user_raises_invalid_credentials(auth_service) -> None:
    service, deps = auth_service
    deps["lockout_store"].is_locked.return_value = None
    deps["user_repo"].find_examiner_by_username.return_value = None
    deps["lockout_store"].record_failure.return_value = LockoutState(
        failed_count=1,
        window_start=datetime.now(UTC),
        locked_until=None,
    )

    with pytest.raises(InvalidCredentialsError):
        service.examiner_login(
            username="nobody",
            password="SecurePass123!",
            client_ip=None,
        )

    deps["audit_service"].log_login_failed.assert_called_once_with(None, None)


def test_examiner_login_inactive_user_raises_invalid_credentials(
    auth_service,
    examiner_user,
) -> None:
    service, deps = auth_service
    examiner_user.is_active = False
    deps["lockout_store"].is_locked.return_value = None
    deps["user_repo"].find_examiner_by_username.return_value = examiner_user
    deps["lockout_store"].record_failure.return_value = LockoutState(
        failed_count=1,
        window_start=datetime.now(UTC),
        locked_until=None,
    )

    with pytest.raises(InvalidCredentialsError):
        service.examiner_login(
            username="examiner1",
            password="SecurePass123!",
            client_ip=None,
        )


def test_examiner_login_locked_before_attempt(auth_service) -> None:
    service, deps = auth_service
    locked_until = datetime.now(UTC) + timedelta(minutes=10)
    deps["lockout_store"].is_locked.return_value = locked_until

    with pytest.raises(AccountLockedError) as exc_info:
        service.examiner_login(
            username="examiner1",
            password="SecurePass123!",
            client_ip=None,
        )

    assert exc_info.value.locked_until == locked_until
    deps["user_repo"].find_examiner_by_username.assert_not_called()


def test_examiner_login_lockout_after_fifth_failure(auth_service, examiner_user) -> None:
    service, deps = auth_service
    locked_until = datetime.now(UTC) + timedelta(minutes=15)
    deps["lockout_store"].is_locked.return_value = None
    deps["user_repo"].find_examiner_by_username.return_value = examiner_user
    deps["lockout_store"].record_failure.return_value = LockoutState(
        failed_count=5,
        window_start=datetime.now(UTC),
        locked_until=locked_until,
    )

    with pytest.raises(AccountLockedError):
        service.examiner_login(
            username="examiner1",
            password="wrong-password",
            client_ip=None,
        )

    deps["audit_service"].log_account_locked.assert_called_once()
