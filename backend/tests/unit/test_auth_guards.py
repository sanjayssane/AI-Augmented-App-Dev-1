"""Unit tests for CSRF and admin authorization dependencies."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.auth import CurrentUser, get_current_user, require_admin_examiner, require_csrf
from app.core.deps import get_auth_service, get_csrf_service, get_settings_service
from app.main import app
from app.models.enums import UserRole
from app.schemas.errors import CsrfValidationError, ForbiddenError
from app.services.csrf_service import CsrfService


@pytest.fixture
def examiner_user() -> CurrentUser:
    return CurrentUser(
        user_id=uuid.uuid4(),
        role=UserRole.EXAMINER,
        session_token="session-token",
        csrf_token="valid-csrf",
    )


def test_require_csrf_rejects_missing_header(examiner_user: CurrentUser) -> None:
    csrf_service = MagicMock(spec=CsrfService)
    csrf_service.validate_token.side_effect = CsrfValidationError()

    with pytest.raises(CsrfValidationError):
        require_csrf(
            current_user=examiner_user,
            csrf_service=csrf_service,
            x_csrf_token=None,
        )


def test_require_csrf_accepts_matching_token(examiner_user: CurrentUser) -> None:
    csrf_service = MagicMock(spec=CsrfService)

    result = require_csrf(
        current_user=examiner_user,
        csrf_service=csrf_service,
        x_csrf_token="valid-csrf",
    )

    assert result is examiner_user
    csrf_service.validate_token.assert_called_once_with("valid-csrf", expected_token="valid-csrf")


def test_require_admin_examiner_rejects_non_admin(examiner_user: CurrentUser) -> None:
    user_repo = MagicMock()
    user = MagicMock()
    user.is_admin = False
    user_repo.find_by_id.return_value = user
    db = MagicMock()

    with pytest.raises(ForbiddenError):
        require_admin_examiner(examiner=examiner_user, db=db, user_repo=user_repo)


def test_require_admin_examiner_accepts_admin(examiner_user: CurrentUser) -> None:
    user_repo = MagicMock()
    user = MagicMock()
    user.is_admin = True
    user_repo.find_by_id.return_value = user
    db = MagicMock()

    result = require_admin_examiner(examiner=examiner_user, db=db, user_repo=user_repo)

    assert result is examiner_user


def test_logout_without_csrf_header_returns_403(examiner_user: CurrentUser) -> None:
    mock_auth_service = MagicMock()
    app.dependency_overrides[get_current_user] = lambda: examiner_user
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    app.dependency_overrides[get_csrf_service] = lambda: CsrfService(csrf_store=MagicMock())
    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/auth/logout")
        assert response.status_code == 403
        mock_auth_service.logout.assert_not_called()
    finally:
        app.dependency_overrides.clear()


def test_patch_settings_rejects_non_admin_examiner(examiner_user: CurrentUser) -> None:
    user_repo = MagicMock()
    user = MagicMock()
    user.is_admin = False
    user_repo.find_by_id.return_value = user

    from app.core.auth import require_csrf, require_examiner
    from app.core.deps import get_db, get_user_repository

    app.dependency_overrides[require_examiner] = lambda: examiner_user
    app.dependency_overrides[require_csrf] = lambda: examiner_user
    app.dependency_overrides[get_settings_service] = lambda: MagicMock()
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_user_repository] = lambda: user_repo
    try:
        with TestClient(app) as client:
            response = client.patch(
                "/api/v1/examiner/settings",
                json={"retention_days_completed": 365},
                headers={"X-CSRF-Token": examiner_user.csrf_token},
            )
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()
