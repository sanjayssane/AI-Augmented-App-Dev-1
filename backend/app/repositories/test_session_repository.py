"""TestSession data access."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.models.enums import SelectionMode, SessionStatus
from app.models.session import Response, SessionQuestion, TestSession


class TestSessionRepository:
    def create_with_questions_and_responses(
        self,
        session: Session,
        *,
        user_id: uuid.UUID,
        selection_mode: SelectionMode,
        start_time: datetime,
        expires_at: datetime,
        questions: list[tuple[uuid.UUID, int]],
    ) -> TestSession:
        test_session = TestSession(
            user_id=user_id,
            status=SessionStatus.ACTIVE,
            selection_mode=selection_mode,
            start_time=start_time,
            last_activity_at=start_time,
            expires_at=expires_at,
        )
        session.add(test_session)
        session.flush()

        for idx, (question_id, version_snapshot) in enumerate(questions, start=1):
            session.add(
                SessionQuestion(
                    session_id=test_session.session_id,
                    question_id=question_id,
                    position=idx,
                    question_version_snapshot=version_snapshot,
                )
            )
            session.add(
                Response(
                    session_id=test_session.session_id,
                    question_id=question_id,
                    selected_option=None,
                    is_correct=None,
                    answered_at=None,
                )
            )

        session.flush()
        return test_session

    def find_active_for_user(self, session: Session, user_id: uuid.UUID) -> TestSession | None:
        now = datetime.now(UTC)
        stmt = (
            select(TestSession)
            .where(
                TestSession.user_id == user_id,
                TestSession.status == SessionStatus.ACTIVE,
                TestSession.expires_at > now,
            )
            .order_by(TestSession.start_time.desc())
            .limit(1)
        )
        return session.scalar(stmt)

    def find_by_id(self, session: Session, session_id: uuid.UUID) -> TestSession | None:
        stmt = select(TestSession).where(TestSession.session_id == session_id)
        return session.scalar(stmt)

    def find_latest_for_user(self, session: Session, user_id: uuid.UUID) -> TestSession | None:
        stmt = (
            select(TestSession)
            .where(TestSession.user_id == user_id)
            .order_by(TestSession.start_time.desc())
            .limit(1)
        )
        return session.scalar(stmt)

    def complete(
        self,
        session: Session,
        test_session: TestSession,
        *,
        score: int | None,
        end_time: datetime,
    ) -> TestSession:
        test_session.status = SessionStatus.COMPLETED
        test_session.score = score
        test_session.end_time = end_time
        test_session.last_activity_at = end_time
        session.flush()
        return test_session

    def list_for_examiner(
        self,
        session: Session,
        *,
        limit: int,
        cursor: uuid.UUID | None = None,
        statuses: list[SessionStatus] | None = None,
    ) -> list[TestSession]:
        stmt = select(TestSession)
        if statuses:
            stmt = stmt.where(TestSession.status.in_(statuses))
        if cursor is not None:
            stmt = stmt.where(TestSession.session_id > cursor)
        stmt = stmt.order_by(TestSession.session_id.asc()).limit(limit)
        return list(session.scalars(stmt).all())

    def expire_stale_active(self, session: Session, *, now: datetime | None = None) -> int:
        at = now or datetime.now(UTC)
        stmt = (
            update(TestSession)
            .where(
                TestSession.status == SessionStatus.ACTIVE,
                TestSession.expires_at <= at,
            )
            .values(status=SessionStatus.EXPIRED, end_time=at)
        )
        result = session.execute(stmt)
        return int(result.rowcount or 0)

    def purge_completed_before(self, session: Session, *, before: datetime) -> int:
        session_ids_stmt = select(TestSession.session_id).where(
            TestSession.status == SessionStatus.COMPLETED,
            TestSession.end_time.is_not(None),
            TestSession.end_time <= before,
        )
        session_ids = list(session.scalars(session_ids_stmt).all())
        if not session_ids:
            return 0

        session.execute(delete(Response).where(Response.session_id.in_(session_ids)))
        session.execute(delete(SessionQuestion).where(SessionQuestion.session_id.in_(session_ids)))
        deleted = session.execute(delete(TestSession).where(TestSession.session_id.in_(session_ids)))
        return int(deleted.rowcount or 0)
