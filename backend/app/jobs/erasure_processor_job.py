"""Background job: process pending GDPR erasure jobs."""

from __future__ import annotations

from app.core.database import SessionLocal
from app.repositories.erasure_job_repository import ErasureJobRepository
from app.repositories.user_repository import UserRepository
from app.services.gdpr_service import GdprService


def run(*, limit: int = 100) -> int:
    with SessionLocal() as db:
        service = GdprService(
            db=db,
            erasure_job_repo=ErasureJobRepository(),
            user_repo=UserRepository(),
        )
        result = service.process_pending_erasure_jobs(limit=limit)
        return result.processed
