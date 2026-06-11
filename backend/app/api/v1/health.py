"""Liveness and readiness probes."""

from fastapi import APIRouter, Response, status
from redis import Redis
from sqlalchemy import create_engine, text

from app.core.config import settings

router = APIRouter()


@router.get(
    "/health",
    summary="Liveness probe",
    response_description="The service process is up.",
    responses={
        200: {
            "content": {"application/json": {"example": {"status": "ok"}}},
        }
    },
)
def health() -> dict[str, str]:
    """Liveness probe — returns 200 as long as the process is running.

    Performs no external dependency checks; use `/ready` for that.
    """
    return {"status": "ok"}


@router.get(
    "/ready",
    summary="Readiness probe",
    response_description="All dependencies (PostgreSQL, Redis) are reachable.",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {"status": "ok", "database": True, "redis": True}
                }
            },
        },
        503: {
            "description": "One or more dependencies are unreachable.",
            "content": {
                "application/json": {
                    "example": {"status": "unavailable", "database": True, "redis": False}
                }
            },
        },
    },
)
def ready(response: Response) -> dict[str, str | bool]:
    """Readiness probe — verifies PostgreSQL and Redis connectivity.

    Returns **503** with per-dependency flags when any check fails, so
    orchestrators can stop routing traffic to this instance.
    """
    checks: dict[str, bool] = {"database": False, "redis": False}

    try:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        pass

    try:
        client = Redis.from_url(settings.redis_url, socket_connect_timeout=2)
        client.ping()
        checks["redis"] = True
    except Exception:
        pass

    if not all(checks.values()):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable", **checks}

    return {"status": "ok", **checks}
