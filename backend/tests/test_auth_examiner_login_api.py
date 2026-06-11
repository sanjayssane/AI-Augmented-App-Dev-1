"""API contract tests for POST /auth/examiner/login."""

from __future__ import annotations

import os
import uuid
from unittest.mock import MagicMock

import fakeredis
import pytest
from app.core.auth import CurrentUser, get_current_user
from app.core.deps import get_auth_service, get_csrf_service, get_db, get_redis
from app.core.passwords import hash_password
from app.main import app
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.platform_settings_repository import PlatformSettingsRepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.redis.lockout_store import LockoutStore
from app.repositories.redis.rate_limit_store import RateLimitStore
from app.repositories.redis.session_store import SessionStore
from app.repositories.response_repository import ResponseRepository
from app.repositories.test_session_repository import TestSessionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import CurrentUserResponse, ExamineeSessionResource
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService, ExaminerLoginResult
from app.services.csrf_service import CsrfIssueResult, CsrfService
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

RUN_DB_TESTS = os.environ.get("RUN_DB_TESTS") == "1"
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://mcq:mcq_dev_password@localhost:5432/mcq_platform",
)


@pytest.fixture
def mock_auth_service() -> MagicMock:
    return MagicMock(spec=AuthService)


@pytest.fixture
def client_with_mock_auth(mock_auth_service: MagicMock) -> TestClient:
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_csrf_service() -> MagicMock:
    return MagicMock(spec=CsrfService)


@pytest.fixture
def client_with_mock_services(mock_auth_service: MagicMock, mock_csrf_service: MagicMock) -> TestClient:
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    app.dependency_overrides[get_csrf_service] = lambda: mock_csrf_service
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_examiner_login_success_response_and_cookie(
    client_with_mock_auth: TestClient,
    mock_auth_service: MagicMock,
) -> None:
    user_id = uuid.uuid4()
    mock_auth_service.examiner_login.return_value = ExaminerLoginResult(
        user_id=user_id,
        username="examiner1",
        must_change_password=False,
        session_token="opaque-session-token",
    )

    response = client_with_mock_auth.post(
        "/api/v1/auth/examiner/login",
        json={"username": "examiner1", "password": "SecurePass123!"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["user_id"] == str(user_id)
    assert body["data"]["username"] == "examiner1"
    assert body["data"]["must_change_password"] is False
    assert "request_id" in body["meta"]
    assert "X-Request-Id" in response.headers

    cookie = response.cookies.get("session_id")
    assert cookie == "opaque-session-token"


def test_examiner_login_invalid_credentials_problem_json(
    client_with_mock_auth: TestClient,
    mock_auth_service: MagicMock,
) -> None:
    from app.schemas.errors import InvalidCredentialsError

    mock_auth_service.examiner_login.side_effect = InvalidCredentialsError()

    response = client_with_mock_auth.post(
        "/api/v1/auth/examiner/login",
        json={"username": "examiner1", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["title"] == "Invalid Credentials"
    assert body["detail"] == "Invalid username or password"
    assert body["status"] == 401
    assert "request_id" in body


def test_examiner_login_account_locked_problem_json(
    client_with_mock_auth: TestClient,
    mock_auth_service: MagicMock,
) -> None:
    from datetime import UTC, datetime, timedelta

    from app.schemas.errors import AccountLockedError

    locked_until = datetime.now(UTC) + timedelta(minutes=15)
    mock_auth_service.examiner_login.side_effect = AccountLockedError(locked_until)

    response = client_with_mock_auth.post(
        "/api/v1/auth/examiner/login",
        json={"username": "examiner1", "password": "wrong"},
    )

    assert response.status_code == 423
    body = response.json()
    assert body["title"] == "Account Locked"
    assert "locked_until" in body


def test_get_csrf_returns_token(
    client_with_mock_services: TestClient,
    mock_csrf_service: MagicMock,
) -> None:
    mock_csrf_service.issue_token.return_value = CsrfIssueResult(token="csrf-token-123")

    response = client_with_mock_services.get("/api/v1/auth/csrf")

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["csrf_token"] == "csrf-token-123"


def test_examinee_entry_returns_created_and_sets_cookie(
    client_with_mock_services: TestClient,
    mock_auth_service: MagicMock,
) -> None:
    session_id = uuid.uuid4()
    mock_auth_service.examinee_entry.return_value = MagicMock(
        created=True,
        session_token="examinee-token",
        session=ExamineeSessionResource(
            session_id=session_id,
            status="ACTIVE",
            total_questions=50,
            answered_count=0,
            current_position=1,
            started_at="2026-06-05T09:30:00Z",
            expires_at="2026-06-05T13:30:00Z",
        ),
    )

    response = client_with_mock_services.post(
        "/api/v1/auth/examinee/entry",
        json={
            "prn": "STU2024001",
            "name": "Jane Doe",
            "privacy_acknowledged": True,
        },
    )

    assert response.status_code == 201
    assert response.cookies.get("session_id") == "examinee-token"
    assert response.json()["data"]["session_id"] == str(session_id)


def test_auth_me_returns_current_user_profile(
    client_with_mock_services: TestClient,
    mock_auth_service: MagicMock,
) -> None:
    current_user = CurrentUser(
        user_id=uuid.uuid4(),
        role=UserRole.EXAMINEE,
        session_token="token-1",
        csrf_token="csrf-1",
    )
    app.dependency_overrides[get_current_user] = lambda: current_user
    mock_auth_service.get_current_user_profile.return_value = CurrentUserResponse(
        user_id=current_user.user_id,
        role=UserRole.EXAMINEE,
        csrf_token=current_user.csrf_token,
        prn="STU2024001",
        name="Jane Doe",
    )

    response = client_with_mock_services.get("/api/v1/auth/me")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["prn"] == "STU2024001"
    assert body["csrf_token"] == current_user.csrf_token
    app.dependency_overrides.pop(get_current_user, None)


def test_auth_logout_clears_cookie(
    client_with_mock_services: TestClient,
    mock_auth_service: MagicMock,
) -> None:
    current_user = CurrentUser(
        user_id=uuid.uuid4(),
        role=UserRole.EXAMINEE,
        session_token="token-2",
        csrf_token="csrf-2",
    )
    from app.core.auth import require_csrf

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[require_csrf] = lambda: current_user
    client_with_mock_services.cookies.set("session_id", "token-2")

    response = client_with_mock_services.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": current_user.csrf_token},
    )

    assert response.status_code == 204
    set_cookie = response.headers.get("set-cookie", "")
    assert "session_id=" in set_cookie
    assert "Max-Age=0" in set_cookie or "max-age=0" in set_cookie
    mock_auth_service.logout.assert_called_once()
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(require_csrf, None)


@pytest.mark.skipif(not RUN_DB_TESTS, reason="Set RUN_DB_TESTS=1 with Postgres")
class TestExaminerLoginIntegration:
    @pytest.fixture
    def integration_client(self) -> TestClient:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        fake_redis = fakeredis.FakeRedis(decode_responses=True)

        def override_get_db():
            db = session_factory()
            try:
                yield db
            finally:
                db.rollback()
                db.close()

        def override_get_redis():
            return fake_redis

        def override_get_auth_service():
            db = session_factory()
            try:
                user_repo = UserRepository()
                session_store = SessionStore(fake_redis)
                lockout_store = LockoutStore(fake_redis)
                audit_service = AuditService(db=db, audit_repo=AuditLogRepository())
                yield AuthService(
                    db=db,
                    user_repo=user_repo,
                    session_store=session_store,
                    lockout_store=lockout_store,
                    audit_service=audit_service,
                    test_session_repo=TestSessionRepository(),
                    question_repo=QuestionRepository(),
                    platform_settings_repo=PlatformSettingsRepository(),
                    rate_limit_store=RateLimitStore(fake_redis),
                    response_repo=ResponseRepository(),
                )
            finally:
                db.rollback()
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_redis] = override_get_redis
        app.dependency_overrides[get_auth_service] = override_get_auth_service

        with TestClient(app) as client:
            yield client

        app.dependency_overrides.clear()
        fake_redis.flushall()
        engine.dispose()

    @pytest.fixture
    def examiner_credentials(self, integration_client: TestClient) -> dict[str, str]:
        username = f"test_exam_{uuid.uuid4().hex[:8]}"
        password = "SecurePass123!"
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        with Session(engine) as db:
            user = User(
                username=username,
                role=UserRole.EXAMINER,
                password_hash=hash_password(password),
                is_active=True,
            )
            db.add(user)
            db.commit()
        engine.dispose()
        return {"username": username, "password": password}

    def test_full_stack_login_success(
        self,
        integration_client: TestClient,
        examiner_credentials: dict[str, str],
    ) -> None:
        response = integration_client.post(
            "/api/v1/auth/examiner/login",
            json=examiner_credentials,
        )
        assert response.status_code == 200
        assert integration_client.cookies.get("session_id") is not None

    def test_full_stack_lockout_after_five_failures(
        self,
        integration_client: TestClient,
        examiner_credentials: dict[str, str],
    ) -> None:
        for _ in range(5):
            response = integration_client.post(
                "/api/v1/auth/examiner/login",
                json={
                    "username": examiner_credentials["username"],
                    "password": "wrong-password",
                },
            )
            assert response.status_code == 401

        locked = integration_client.post(
            "/api/v1/auth/examiner/login",
            json=examiner_credentials,
        )
        assert locked.status_code == 423
        assert "locked_until" in locked.json()
