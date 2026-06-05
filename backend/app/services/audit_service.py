"""Audit event emission."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.enums import AuditOutcome
from app.repositories.audit_log_repository import AuditLogRepository


class AuditService:
    def __init__(self, db: Session, audit_repo: AuditLogRepository) -> None:
        self._db = db
        self._audit_repo = audit_repo

    def log_login_success(self, user_id: uuid.UUID, ip_address: str | None) -> None:
        self.log_event(
            event_type="LOGIN_SUCCESS",
            outcome=AuditOutcome.SUCCESS,
            actor_id=user_id,
            resource_type="User",
            resource_id=user_id,
            ip_address=ip_address,
        )

    def log_login_failed(
        self,
        user_id: uuid.UUID | None,
        ip_address: str | None,
    ) -> None:
        self.log_event(
            event_type="LOGIN_FAILED",
            outcome=AuditOutcome.FAILURE,
            actor_id=user_id,
            resource_type="User" if user_id else None,
            resource_id=user_id,
            ip_address=ip_address,
        )

    def log_account_locked(self, user_id: uuid.UUID | None, ip_address: str | None) -> None:
        self.log_event(
            event_type="ACCOUNT_LOCKED",
            outcome=AuditOutcome.FAILURE,
            actor_id=user_id,
            resource_type="User" if user_id else None,
            resource_id=user_id,
            ip_address=ip_address,
        )

    def log_event(
        self,
        *,
        event_type: str,
        outcome: AuditOutcome,
        actor_id: uuid.UUID | None = None,
        resource_type: str | None = None,
        resource_id: uuid.UUID | None = None,
        ip_address: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        self._audit_repo.append(
            self._db,
            event_type=event_type,
            outcome=outcome,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            metadata=metadata,
        )
        self._db.commit()

    def log_question_event(
        self,
        *,
        event_type: str,
        actor_id: uuid.UUID,
        question_id: uuid.UUID,
        outcome: AuditOutcome = AuditOutcome.SUCCESS,
        ip_address: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        self.log_event(
            event_type=event_type,
            outcome=outcome,
            actor_id=actor_id,
            resource_type="Question",
            resource_id=question_id,
            ip_address=ip_address,
            metadata=metadata,
        )

    def log_results_viewed(
        self,
        *,
        actor_id: uuid.UUID,
        session_id: uuid.UUID,
        ip_address: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        self.log_event(
            event_type="RESULTS_VIEWED",
            outcome=AuditOutcome.SUCCESS,
            actor_id=actor_id,
            resource_type="TestSession",
            resource_id=session_id,
            ip_address=ip_address,
            metadata=metadata,
        )

    def log_results_exported(
        self,
        *,
        actor_id: uuid.UUID,
        session_id: uuid.UUID | None = None,
        ip_address: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        self.log_event(
            event_type="RESULTS_EXPORTED",
            outcome=AuditOutcome.SUCCESS,
            actor_id=actor_id,
            resource_type="TestSession" if session_id else None,
            resource_id=session_id,
            ip_address=ip_address,
            metadata=metadata,
        )
