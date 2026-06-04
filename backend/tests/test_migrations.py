"""Database migration and constraint integration tests."""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from app.models.enums import SelectionMode, SessionStatus, UserRole
from app.models.session import TestSession as TestSessionModel
from app.models.settings import PlatformSettings
from app.models.user import User
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

RUN_DB_TESTS = os.environ.get("RUN_DB_TESTS") == "1"
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://mcq:mcq_dev_password@localhost:5432/mcq_platform",
)


pytestmark = pytest.mark.skipif(not RUN_DB_TESTS, reason="Set RUN_DB_TESTS=1 with Postgres")


@pytest.fixture(scope="module")
def db_engine():
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    with Session(db_engine) as session:
        yield session
        session.rollback()


def test_platform_settings_seeded(db_session: Session) -> None:
    keys = set(db_session.scalars(select(PlatformSettings.setting_key)).all())
    assert "retention_days_completed" in keys
    assert "allow_examinee_retake" in keys
    assert "question_selection_mode" in keys

    retention = db_session.get(PlatformSettings, "retention_days_completed")
    assert retention is not None
    assert retention.setting_value == 730


def test_one_active_session_per_user(db_session: Session) -> None:
    user_id = uuid.uuid4()
    now = datetime.now(UTC)
    expires = now + timedelta(hours=24)

    db_session.add(
        User(
            user_id=user_id,
            role=UserRole.EXAMINEE,
            prn_ciphertext="enc",
            prn_lookup_hash=f"hash-{uuid.uuid4().hex}",
            name_ciphertext="name-enc",
            is_active=True,
        )
    )
    db_session.flush()

    for _ in range(2):
        db_session.add(
            TestSessionModel(
                user_id=user_id,
                status=SessionStatus.ACTIVE,
                selection_mode=SelectionMode.FIXED_ORDER,
                start_time=now,
                last_activity_at=now,
                expires_at=expires,
            )
        )
        db_session.flush()

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_examinee_prn_unique_among_active(db_session: Session) -> None:
    prn_hash = f"dup-{uuid.uuid4().hex[:16]}"
    for _ in range(2):
        db_session.add(
            User(
                user_id=uuid.uuid4(),
                role=UserRole.EXAMINEE,
                prn_ciphertext="enc",
                prn_lookup_hash=prn_hash,
                name_ciphertext="name-enc",
                is_active=True,
            )
        )
        db_session.flush()

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_audit_schema_exists(db_engine) -> None:
    with db_engine.connect() as conn:
        result = conn.execute(
            text(
                """
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'audit' AND table_name = 'audit_logs'
                """
            )
        )
        assert result.scalar() == 1
