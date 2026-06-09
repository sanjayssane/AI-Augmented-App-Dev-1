"""User data access."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.encryption import encrypt_field, prn_lookup_hash
from app.models.enums import UserRole
from app.models.user import User


class UserRepository:
    def find_examiner_by_username(self, session: Session, username: str) -> User | None:
        stmt = select(User).where(
            User.role == UserRole.EXAMINER,
            User.username == username,
            User.deleted_at.is_(None),
        )
        return session.scalar(stmt)

    def find_by_prn_hash(self, session: Session, prn_hash: str) -> User | None:
        stmt = select(User).where(
            User.role == UserRole.EXAMINEE,
            User.prn_lookup_hash == prn_hash,
            User.deleted_at.is_(None),
        )
        return session.scalar(stmt)

    def create_examinee(
        self,
        session: Session,
        *,
        prn: str,
        name: str,
        is_active: bool = True,
        privacy_acknowledged_at: datetime | None = None,
    ) -> User:
        user = User(
            role=UserRole.EXAMINEE,
            prn_ciphertext=encrypt_field(prn),
            prn_lookup_hash=prn_lookup_hash(prn),
            name_ciphertext=encrypt_field(name),
            is_active=is_active,
            privacy_acknowledged_at=privacy_acknowledged_at,
        )
        session.add(user)
        session.flush()
        return user

    def count_examiners(self, session: Session) -> int:
        stmt = select(func.count()).select_from(User).where(
            User.role == UserRole.EXAMINER,
            User.deleted_at.is_(None),
        )
        return session.scalar(stmt) or 0

    def create_examiner(
        self,
        session: Session,
        *,
        username: str,
        password_hash: str,
        is_active: bool = True,
        is_admin: bool = False,
    ) -> User:
        user = User(
            role=UserRole.EXAMINER,
            username=username.strip(),
            password_hash=password_hash,
            is_active=is_active,
            is_admin=is_admin,
        )
        session.add(user)
        session.flush()
        return user

    def find_by_id(self, session: Session, user_id: uuid.UUID) -> User | None:
        stmt = select(User).where(
            User.user_id == user_id,
            User.deleted_at.is_(None),
        )
        return session.scalar(stmt)

    def anonymise_user(self, session: Session, user: User) -> User:
        now = datetime.now(UTC)
        user.is_active = False
        user.deleted_at = now

        if user.role == UserRole.EXAMINEE:
            anonymised_marker = f"anonymised:{user.user_id}"
            user.prn_ciphertext = encrypt_field(anonymised_marker)
            user.prn_lookup_hash = prn_lookup_hash(anonymised_marker)
            user.name_ciphertext = encrypt_field("ANONYMISED")
        else:
            user.username = f"anonymised-{uuid.uuid4().hex[:12]}"
            user.password_hash = user.password_hash or "ANONYMISED"

        session.flush()
        return user
