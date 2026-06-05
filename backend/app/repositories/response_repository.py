"""Response data access."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.enums import SelectedOption
from app.models.session import Response


class ResponseRepository:
    def update_selection(
        self,
        session: Session,
        response: Response,
        *,
        selected_option: SelectedOption,
        answered_at: datetime | None = None,
    ) -> Response:
        response.selected_option = selected_option
        response.answered_at = answered_at or datetime.now(UTC)
        session.flush()
        return response

    def bulk_set_correctness(
        self,
        session: Session,
        *,
        session_id: uuid.UUID,
        correctness_by_question_id: dict[uuid.UUID, bool],
    ) -> int:
        if not correctness_by_question_id:
            return 0

        updated = 0
        for question_id, is_correct in correctness_by_question_id.items():
            stmt = (
                update(Response)
                .where(
                    Response.session_id == session_id,
                    Response.question_id == question_id,
                )
                .values(is_correct=is_correct)
            )
            result = session.execute(stmt)
            updated += int(result.rowcount or 0)
        return updated

    def count_answered(self, session: Session, *, session_id: uuid.UUID) -> int:
        stmt = select(func.count(Response.response_id)).where(
            Response.session_id == session_id,
            Response.selected_option.is_not(None),
        )
        return int(session.scalar(stmt) or 0)

    def get_for_session(self, session: Session, *, session_id: uuid.UUID) -> list[Response]:
        stmt = (
            select(Response)
            .where(Response.session_id == session_id)
            .order_by(Response.question_id.asc())
        )
        return list(session.scalars(stmt).all())
