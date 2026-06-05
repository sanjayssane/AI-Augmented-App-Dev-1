"""Append-only audit log data access."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.enums import AuditOutcome


class AuditLogRepository:
    def append(
        self,
        session: Session,
        *,
        event_type: str,
        outcome: AuditOutcome,
        actor_id: uuid.UUID | None = None,
        resource_type: str | None = None,
        resource_id: uuid.UUID | None = None,
        ip_address: str | None = None,
        metadata: dict | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            event_type=event_type,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            ip_address=ip_address,
            metadata_=metadata or {},
        )
        session.add(entry)
        session.flush()
        return entry
