"""Unit tests for AuthService.examinee_entry and profile/logout helpers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from app.models.enums import SelectionMode, SessionStatus, UserRole
from app.models.session import TestSession
from app.models.user import User
from app.schemas.errors import (
    ExamAlreadyCompletedError,
    IdentityMismatchError,
    InsufficientQuestionBankError,
    RateLimitExceededError,
)
from app.services.auth_service import AuthService


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


def _make_examinee() -> User:
    return User(
        user_id=uuid.uuid4(),
        role=UserRole.EXAMINEE,
        prn_ciphertext="enc-prn",
        prn_lookup_hash="hashed-prn",
        name_ciphertext="enc-name",
        is_active=True,
        privacy_acknowledged_at=datetime.now(UTC),
    )


def _make_session(user_id: uuid.UUID, status: SessionStatus) -> TestSession:
    now = datetime.now(UTC)
    return TestSession(
        session_id=uuid.uuid4(),
        user_id=user_id,
        status=status,
        selection_mode=SelectionMode.FIXED_ORDER,
        start_time=now,
        last_activity_at=now,
        expires_at=now,
    )


def test_examinee_entry_creates_new_user_and_session(auth_service) -> None:
    service, deps = auth_service
    user = _make_examinee()
    new_session = _make_session(user.user_id, SessionStatus.ACTIVE)

    deps["rate_limit_store"].check_and_increment.return_value = (True, 0)
    deps["user_repo"].find_by_prn_hash.return_value = None
    deps["user_repo"].create_examinee.return_value = user
    deps["question_repo"].count_active.return_value = 50
    deps["platform_settings_repo"].get_value.return_value = "FIXED_ORDER"
    deps["question_repo"].list_active_for_selection.return_value = [MagicMock() for _ in range(50)]
    for idx, question in enumerate(deps["question_repo"].list_active_for_selection.return_value):
        question.question_id = uuid.uuid4()
        question.question_version = 1 + idx
    deps["test_session_repo"].create_with_questions_and_responses.return_value = new_session
    deps["session_store"].create_session.return_value = "session-token"
    deps["response_repo"].count_answered.return_value = 0

    result = service.examinee_entry(
        prn="STU2024001",
        name="Jane Doe",
        privacy_acknowledged=True,
        client_ip="127.0.0.1",
    )

    assert result.created is True
    assert result.session.status == SessionStatus.ACTIVE
    assert result.session_token == "session-token"
    deps["db"].commit.assert_called_once()


def test_examinee_entry_resumes_active_session(auth_service) -> None:
    service, deps = auth_service
    user = _make_examinee()
    active_session = _make_session(user.user_id, SessionStatus.ACTIVE)

    deps["rate_limit_store"].check_and_increment.return_value = (True, 0)
    deps["user_repo"].find_by_prn_hash.return_value = user
    deps["test_session_repo"].find_active_for_user.return_value = active_session
    deps["session_store"].create_session.return_value = "resume-token"
    deps["response_repo"].count_answered.return_value = 7

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("app.services.auth_service.decrypt_field", lambda _: "Jane Doe")
        result = service.examinee_entry(
            prn="STU2024001",
            name="Jane Doe",
            privacy_acknowledged=True,
            client_ip="127.0.0.1",
        )

    assert result.created is False
    assert result.session.answered_count == 7
    deps["test_session_repo"].find_latest_for_user.assert_not_called()


def test_examinee_entry_completed_without_retake_raises_conflict(auth_service) -> None:
    service, deps = auth_service
    user = _make_examinee()
    completed_session = _make_session(user.user_id, SessionStatus.COMPLETED)

    deps["rate_limit_store"].check_and_increment.return_value = (True, 0)
    deps["user_repo"].find_by_prn_hash.return_value = user
    deps["test_session_repo"].find_active_for_user.return_value = None
    deps["test_session_repo"].find_latest_for_user.return_value = completed_session
    deps["platform_settings_repo"].get_value.return_value = False

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("app.services.auth_service.decrypt_field", lambda _: "Jane Doe")
        with pytest.raises(ExamAlreadyCompletedError):
            service.examinee_entry(
                prn="STU2024001",
                name="Jane Doe",
                privacy_acknowledged=True,
                client_ip="127.0.0.1",
            )


def test_examinee_entry_name_mismatch_raises_forbidden(auth_service) -> None:
    service, deps = auth_service
    user = _make_examinee()

    deps["rate_limit_store"].check_and_increment.return_value = (True, 0)
    deps["user_repo"].find_by_prn_hash.return_value = user

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("app.services.auth_service.decrypt_field", lambda _: "Another Name")
        with pytest.raises(IdentityMismatchError):
            service.examinee_entry(
                prn="STU2024001",
                name="Jane Doe",
                privacy_acknowledged=True,
                client_ip="127.0.0.1",
            )


def test_examinee_entry_rate_limited(auth_service) -> None:
    service, deps = auth_service
    deps["rate_limit_store"].check_and_increment.return_value = (False, 30)

    with pytest.raises(RateLimitExceededError):
        service.examinee_entry(
            prn="STU2024001",
            name="Jane Doe",
            privacy_acknowledged=True,
            client_ip="127.0.0.1",
        )


def test_examinee_entry_requires_minimum_question_bank(auth_service) -> None:
    service, deps = auth_service
    user = _make_examinee()

    deps["rate_limit_store"].check_and_increment.return_value = (True, 0)
    deps["user_repo"].find_by_prn_hash.return_value = None
    deps["user_repo"].create_examinee.return_value = user
    deps["question_repo"].count_active.return_value = 49

    with pytest.raises(InsufficientQuestionBankError):
        service.examinee_entry(
            prn="STU2024001",
            name="Jane Doe",
            privacy_acknowledged=True,
            client_ip="127.0.0.1",
        )
