"""Liveness and readiness probes."""

from fastapi import APIRouter, Response, status
from redis import Redis
from sqlalchemy import create_engine, text

from app.core.config import settings

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness probe — no external dependencies."""
    return {"status": "ok"}


@router.get("/ready")
def ready(response: Response) -> dict[str, str | bool]:
    """Readiness probe — PostgreSQL and Redis connectivity."""
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
