"""ErasureJob data access."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import ErasureJobStatus
from app.models.erasure import ErasureJob


class ErasureJobRepository:
    def create(
        self,
        session: Session,
        *,
        examinee_user_id: uuid.UUID,
        operator_user_id: uuid.UUID,
    ) -> ErasureJob:
        job = ErasureJob(
            examinee_user_id=examinee_user_id,
            operator_user_id=operator_user_id,
            status=ErasureJobStatus.PENDING,
        )
        session.add(job)
        session.flush()
        return job

    def mark_completed(self, session: Session, job: ErasureJob) -> ErasureJob:
        job.status = ErasureJobStatus.COMPLETED
        job.completed_at = datetime.now(UTC)
        session.flush()
        return job

    def find_pending(self, session: Session, *, limit: int = 100) -> list[ErasureJob]:
        stmt = (
            select(ErasureJob)
            .where(ErasureJob.status == ErasureJobStatus.PENDING)
            .order_by(ErasureJob.requested_at.asc())
            .limit(limit)
        )
        return list(session.scalars(stmt).all())
