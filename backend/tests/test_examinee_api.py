"""API contract tests for examinee endpoints with mocked services."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
import app.services.test_session_service as test_session_service_module
from app.core.auth import CurrentUser
from app.core.deps import get_gdpr_service, get_scoring_service, get_test_session_service
from app.main import app
from app.models.enums import CorrectOption, SelectedOption, SessionStatus, UserRole
from app.services.gdpr_service import ExportDataResult, GdprService
from app.services.scoring_service import ScoringService, SubmitSessionView
from app.services.test_session_service import (
    QuestionAtPositionView,
    ReviewItemView,
    SaveResponseView,
    SessionView,
)
from fastapi.testclient import TestClient


@pytest.fixture
def mock_test_session_service() -> MagicMock:
    return MagicMock(spec=test_session_service_module.TestSessionService)


@pytest.fixture
def mock_scoring_service() -> MagicMock:
    return MagicMock(spec=ScoringService)


@pytest.fixture
def mock_gdpr_service() -> MagicMock:
    return MagicMock(spec=GdprService)


@pytest.fixture
def examinee_user() -> CurrentUser:
    return CurrentUser(
        user_id=uuid.uuid4(),
        role=UserRole.EXAMINEE,
        session_token="test-token",
        csrf_token="test-csrf",
    )


@pytest.fixture
def client_with_mocks(
    mock_test_session_service: MagicMock,
    mock_scoring_service: MagicMock,
    mock_gdpr_service: MagicMock,
    examinee_user: CurrentUser,
) -> TestClient:
    from app.core.auth import require_examinee

    app.dependency_overrides[get_test_session_service] = lambda: mock_test_session_service
    app.dependency_overrides[get_scoring_service] = lambda: mock_scoring_service
    app.dependency_overrides[get_gdpr_service] = lambda: mock_gdpr_service
    app.dependency_overrides[require_examinee] = lambda: examinee_user
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_get_current_session_returns_resource(
    client_with_mocks: TestClient,
    mock_test_session_service: MagicMock,
) -> None:
    session_id = uuid.uuid4()
    now = datetime.now(UTC)
    mock_test_session_service.get_current_session.return_value = SessionView(
        session_id=session_id,
        status=SessionStatus.ACTIVE,
        answered_count=7,
        current_position=1,
        started_at=now,
        expires_at=now + timedelta(hours=4),
    )

    response = client_with_mocks.get("/api/v1/examinee/sessions/current")

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["session_id"] == str(session_id)
    assert body["data"]["status"] == "ACTIVE"
    assert body["data"]["answered_count"] == 7


def test_get_question_at_position_no_correct_option_leak(
    client_with_mocks: TestClient,
    mock_test_session_service: MagicMock,
) -> None:
    session_id = uuid.uuid4()
    question_id = uuid.uuid4()
    mock_test_session_service.get_question_at_position.return_value = QuestionAtPositionView(
        position=7,
        total=50,
        question_id=question_id,
        question_text="What is Python?",
        option_a="Snake",
        option_b="Language",
        option_c="Planet",
        option_d="Car",
        selected_option=SelectedOption.B,
        answered_count=12,
    )

    response = client_with_mocks.get(f"/api/v1/examinee/sessions/{session_id}/questions/7")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["position"] == 7
    assert body["question"]["question_id"] == str(question_id)
    assert "correct_option" not in body["question"]
    assert body["selected_option"] == "B"


def test_save_response_contract(
    client_with_mocks: TestClient,
    mock_test_session_service: MagicMock,
) -> None:
    session_id = uuid.uuid4()
    question_id = uuid.uuid4()
    now = datetime.now(UTC)
    mock_test_session_service.save_response.return_value = SaveResponseView(
        question_id=question_id,
        selected_option=SelectedOption.C,
        updated_at=now,
        answered_count=33,
    )

    response = client_with_mocks.put(
        f"/api/v1/examinee/sessions/{session_id}/responses/{question_id}",
        headers={"If-Unmodified-Since": now.isoformat()},
        json={"selected_option": "C"},
    )

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["question_id"] == str(question_id)
    assert body["selected_option"] == "C"
    assert body["answered_count"] == 33


def test_submit_session_contract(
    client_with_mocks: TestClient,
    mock_scoring_service: MagicMock,
) -> None:
    session_id = uuid.uuid4()
    submitted_at = datetime.now(UTC)
    mock_scoring_service.submit_session.return_value = SubmitSessionView(
        session_id=session_id,
        status=SessionStatus.COMPLETED,
        score=38,
        max_score=50,
        correct_count=38,
        incorrect_count=10,
        unattempted_count=2,
        submitted_at=submitted_at,
    )

    response = client_with_mocks.post(
        f"/api/v1/examinee/sessions/{session_id}/submit",
        headers={"Idempotency-Key": str(uuid.uuid4())},
        json={"confirm": True},
    )

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["status"] == "COMPLETED"
    assert body["score"] == 38
    assert body["max_score"] == 50


def test_get_review_returns_correct_option_after_completion(
    client_with_mocks: TestClient,
    mock_test_session_service: MagicMock,
) -> None:
    session_id = uuid.uuid4()
    mock_test_session_service.get_review.return_value = [
        ReviewItemView(
            position=1,
            question_text="Question?",
            option_a="A1",
            option_b="B1",
            option_c="C1",
            option_d="D1",
            selected_option=SelectedOption.B,
            correct_option=CorrectOption.C,
            is_correct=False,
        )
    ]

    response = client_with_mocks.get(f"/api/v1/examinee/sessions/{session_id}/review")

    assert response.status_code == 200
    item = response.json()["data"]["items"][0]
    assert item["selected_option"] == "B"
    assert item["correct_option"] == "C"
    assert item["is_correct"] is False


def test_data_export_attachment_response(
    client_with_mocks: TestClient,
    mock_gdpr_service: MagicMock,
) -> None:
    payload = {"user": {"user_id": str(uuid.uuid4())}, "sessions": []}
    mock_gdpr_service.export_examinee_data.return_value = ExportDataResult(
        filename="my-data-export.json",
        json_payload=json.dumps(payload),
    )

    response = client_with_mocks.get("/api/v1/examinee/me/data-export")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.headers["content-disposition"] == 'attachment; filename="my-data-export.json"'
    assert response.json() == payload
