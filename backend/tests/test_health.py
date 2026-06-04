"""Smoke tests for scaffold health endpoints."""

import os

import pytest
from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_available(client: TestClient) -> None:
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "MCQ Online Test Platform API"


@pytest.mark.skipif(
    os.getenv("SKIP_READY_TEST", "1") == "1",
    reason="Requires running Postgres and Redis (set SKIP_READY_TEST=0 to enable)",
)
def test_ready_when_dependencies_up(client: TestClient) -> None:
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] is True
    assert body["redis"] is True
