"""GDPR access export and erasure workflows."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.encryption import decrypt_field
from app.models.enums import ErasureJobStatus, UserRole
from app.models.session import Response, TestSession
from app.repositories.erasure_job_repository import ErasureJobRepository
from app.repositories.user_repository import UserRepository
from app.schemas.errors import ForbiddenError, NotFoundError


@dataclass
class ExportDataResult:
    filename: str
    json_payload: str


class GdprService:
    def __init__(
        self,
        db: Session,
        user_repo: UserRepository,
        erasure_job_repo: ErasureJobRepository,
    ) -> None:
        self._db = db
        self._user_repo = user_repo
        self._erasure_job_repo = erasure_job_repo

    def export_examinee_data(self, *, user_id: uuid.UUID) -> ExportDataResult:
        user = self._user_repo.find_by_id(self._db, user_id)
        if user is None or user.role != UserRole.EXAMINEE:
            raise NotFoundError("Examinee was not found.")

        sessions = self._db.scalars(
            select(TestSession)
            .where(TestSession.user_id == user.user_id)
            .order_by(TestSession.start_time.asc())
        ).all()

        export = {
            "user": {
                "user_id": str(user.user_id),
                "role": user.role.value,
                "prn": decrypt_field(user.prn_ciphertext) if user.prn_ciphertext else None,
                "name": decrypt_field(user.name_ciphertext) if user.name_ciphertext else None,
                "is_active": user.is_active,
                "privacy_acknowledged_at": user.privacy_acknowledged_at.isoformat()
                if user.privacy_acknowledged_at
                else None,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat(),
                "deleted_at": user.deleted_at.isoformat() if user.deleted_at else None,
            },
            "sessions": [],
        }
        for test_session in sessions:
            responses = self._db.scalars(
                select(Response)
                .where(Response.session_id == test_session.session_id)
                .order_by(Response.question_id.asc())
            ).all()
            export["sessions"].append(
                {
                    "session_id": str(test_session.session_id),
                    "status": test_session.status.value,
                    "selection_mode": test_session.selection_mode.value,
                    "score": test_session.score,
                    "start_time": test_session.start_time.isoformat(),
                    "end_time": test_session.end_time.isoformat() if test_session.end_time else None,
                    "last_activity_at": test_session.last_activity_at.isoformat(),
                    "expires_at": test_session.expires_at.isoformat(),
                    "created_at": test_session.created_at.isoformat(),
                    "responses": [
                        {
                            "response_id": str(response.response_id),
                            "question_id": str(response.question_id),
                            "selected_option": response.selected_option.value
                            if response.selected_option
                            else None,
                            "is_correct": response.is_correct,
                            "answered_at": response.answered_at.isoformat()
                            if response.answered_at
                            else None,
                            "updated_at": response.updated_at.isoformat(),
                        }
                        for response in responses
                    ],
                }
            )
        payload = json.dumps(export, ensure_ascii=True, indent=2)
        return ExportDataResult(filename="my-data-export.json", json_payload=payload)

    def request_erasure(self, *, examinee_user_id: uuid.UUID, operator_user_id: uuid.UUID) -> uuid.UUID:
        examinee = self._user_repo.find_by_id(self._db, examinee_user_id)
        if examinee is None or examinee.role != UserRole.EXAMINEE:
            raise NotFoundError("Examinee was not found.")
        operator = self._user_repo.find_by_id(self._db, operator_user_id)
        if operator is None or operator.role != UserRole.EXAMINER:
            raise ForbiddenError("Only examiners can request erasure jobs.")
        job = self._erasure_job_repo.create(
            self._db,
            examinee_user_id=examinee_user_id,
            operator_user_id=operator_user_id,
        )
        self._db.commit()
        return job.job_id

    def process_pending_erasure_jobs(self, *, limit: int = 100) -> int:
        jobs = self._erasure_job_repo.find_pending(self._db, limit=limit)
        processed = 0
        for job in jobs:
            user = self._user_repo.find_by_id(self._db, job.examinee_user_id)
            if user is not None and user.role == UserRole.EXAMINEE:
                self._user_repo.anonymise_user(self._db, user)
                self._erasure_job_repo.mark_completed(self._db, job)
                processed += 1
            else:
                job.status = ErasureJobStatus.FAILED
                job.completed_at = datetime.now(UTC)
        self._db.commit()
        return processed
