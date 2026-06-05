"""Basic contract tests for examiner endpoints with mocked services."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.core.auth import CurrentUser, require_examiner
from app.core.deps import (
    get_question_service,
    get_results_service,
    get_settings_service,
    get_user_admin_service,
)
from app.main import app
from app.models.enums import CorrectOption, SelectedOption, SelectionMode, SessionStatus, UserRole


class _QuestionServiceMock:
    def list_questions(self, *, limit: int, cursor, include_deleted: bool):
        row = type(
            "QuestionRow",
            (),
            {
                "question_id": uuid.uuid4(),
                "question_text": "What is 2+2?",
                "option_a": "1",
                "option_b": "2",
                "option_c": "3",
                "option_d": "4",
                "correct_option": CorrectOption.D,
                "question_version": 1,
                "is_deleted": False,
                "updated_at": datetime.now(UTC),
            },
        )()
        return [row], None, 55

    def create_question(self, *, payload, created_by):
        return type(
            "QuestionRow",
            (),
            {
                "question_id": uuid.uuid4(),
                "question_text": payload.question_text,
                "option_a": payload.option_a,
                "option_b": payload.option_b,
                "option_c": payload.option_c,
                "option_d": payload.option_d,
                "correct_option": payload.correct_option,
                "question_version": 1,
                "is_deleted": False,
                "updated_at": datetime.now(UTC),
            },
        )()

    def get_question(self, *, question_id):
        return type(
            "QuestionRow",
            (),
            {
                "question_id": question_id,
                "question_text": "Base text",
                "option_a": "A",
                "option_b": "B",
                "option_c": "C",
                "option_d": "D",
                "correct_option": CorrectOption.A,
                "question_version": 1,
                "is_deleted": False,
                "updated_at": datetime.now(UTC),
            },
        )()

    def patch_question(self, *, question_id, actor_id, payload):
        return type(
            "QuestionRow",
            (),
            {
                "question_id": question_id,
                "question_text": payload.question_text,
                "option_a": payload.option_a,
                "option_b": payload.option_b,
                "option_c": payload.option_c,
                "option_d": payload.option_d,
                "correct_option": payload.correct_option,
                "question_version": 2,
                "is_deleted": False,
                "updated_at": datetime.now(UTC),
            },
        )()

    def delete_question(self, *, question_id):
        return None


class _ResultsServiceMock:
    def list_sessions(self, *, limit: int, cursor):
        return (
            [
                type(
                    "SessionSummary",
                    (),
                    {
                        "session_id": uuid.uuid4(),
                        "status": SessionStatus.COMPLETED,
                        "score": 45,
                        "submitted_at": datetime.now(UTC),
                        "prn": "PRN001",
                        "name": "Jane",
                    },
                )()
            ],
            None,
        )

    def get_session_detail(self, *, session_id):
        return type(
            "SessionDetail",
            (),
            {
                "session_id": session_id,
                "status": SessionStatus.COMPLETED,
                "score": 45,
                "started_at": datetime.now(UTC),
                "submitted_at": datetime.now(UTC),
                "selection_mode": SelectionMode.FIXED_ORDER,
                "prn": "PRN001",
                "name": "Jane",
                "responses": [
                    type(
                        "QuestionResult",
                        (),
                        {
                            "question_id": uuid.uuid4(),
                            "position": 1,
                            "question_text": "What is 2+2?",
                            "selected_option": SelectedOption.D,
                            "correct_option": CorrectOption.D,
                            "is_correct": True,
                        },
                    )()
                ],
            },
        )()

    def export_sessions_csv(self, *, anonymised: bool = False):
        header = "session_id,score\n" if anonymised else "session_id,prn,name,score\n"
        return "\ufeff" + header + "abc,45\n"


class _SettingsServiceMock:
    def get_settings(self):
        return type(
            "SettingsView",
            (),
            {
                "retention_days_completed": 730,
                "allow_examinee_retake": False,
                "question_selection_mode": SelectionMode.FIXED_ORDER,
            },
        )()

    def patch_settings(
        self,
        *,
        retention_days_completed=None,
        allow_examinee_retake=None,
        question_selection_mode=None,
    ):
        return type(
            "SettingsView",
            (),
            {
                "retention_days_completed": retention_days_completed or 730,
                "allow_examinee_retake": (
                    allow_examinee_retake if allow_examinee_retake is not None else False
                ),
                "question_selection_mode": question_selection_mode or SelectionMode.FIXED_ORDER,
            },
        )()


class _UserAdminServiceMock:
    def create_examiner(self, *, username: str, password: str, force_password_change: bool = True):
        return type(
            "ExaminerCreated",
            (),
            {
                "user_id": uuid.uuid4(),
                "username": username.strip(),
                "is_active": True,
                "force_password_change": force_password_change,
                "created_at": datetime.now(UTC),
            },
        )()


@pytest.fixture
def examiner_client() -> TestClient:
    mock_user = CurrentUser(
        user_id=uuid.uuid4(),
        role=UserRole.EXAMINER,
        session_token="session-token",
        csrf_token="csrf-token",
    )
    app.dependency_overrides[require_examiner] = lambda: mock_user

    app.dependency_overrides[get_question_service] = lambda: _QuestionServiceMock()
    app.dependency_overrides[get_results_service] = lambda: _ResultsServiceMock()
    app.dependency_overrides[get_settings_service] = lambda: _SettingsServiceMock()
    app.dependency_overrides[get_user_admin_service] = lambda: _UserAdminServiceMock()
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_examiner_questions_contract(examiner_client: TestClient) -> None:
    list_response = examiner_client.get("/api/v1/examiner/questions")
    assert list_response.status_code == 200
    assert "items" in list_response.json()["data"]

    create_response = examiner_client.post(
        "/api/v1/examiner/questions",
        json={
            "question_text": "Q?",
            "option_a": "A",
            "option_b": "B",
            "option_c": "C",
            "option_d": "D",
            "correct_option": "A",
        },
    )
    assert create_response.status_code == 201


def test_examiner_sessions_contract(examiner_client: TestClient) -> None:
    list_response = examiner_client.get("/api/v1/examiner/sessions")
    assert list_response.status_code == 200
    session_id = list_response.json()["data"]["items"][0]["session_id"]

    detail_response = examiner_client.get(f"/api/v1/examiner/sessions/{session_id}")
    assert detail_response.status_code == 200
    assert "responses" in detail_response.json()["data"]

    export_response = examiner_client.get("/api/v1/examiner/sessions/export")
    assert export_response.status_code == 200
    assert export_response.text.startswith("\ufeff")


def test_examiner_settings_contract(examiner_client: TestClient) -> None:
    get_response = examiner_client.get("/api/v1/examiner/settings")
    assert get_response.status_code == 200
    assert "retention_days_completed" in get_response.json()["data"]

    patch_response = examiner_client.patch(
        "/api/v1/examiner/settings",
        json={"retention_days_completed": 365},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["data"]["retention_days_completed"] == 365


def test_examiner_users_contract(examiner_client: TestClient) -> None:
    create_response = examiner_client.post(
        "/api/v1/examiner/users/examiners",
        json={"username": "new_examiner", "password": "SecurePass123!", "force_password_change": True},
    )
    assert create_response.status_code == 201
    assert create_response.json()["data"]["username"] == "new_examiner"

    erase_response = examiner_client.post(f"/api/v1/examiner/users/examinees/{uuid.uuid4()}/erase")
    assert erase_response.status_code == 202
