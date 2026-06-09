"""Examiner user administration use cases."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.passwords import hash_password
from app.domain.validation import validate_password
from app.repositories.user_repository import UserRepository
from app.schemas.errors import ConflictError


@dataclass
class ExaminerUserCreated:
    user_id: uuid.UUID
    username: str
    is_active: bool
    force_password_change: bool
    created_at: object


class UserAdminService:
    def __init__(self, db: Session, user_repo: UserRepository) -> None:
        self._db = db
        self._user_repo = user_repo

    def create_examiner(
        self,
        *,
        username: str,
        password: str,
        force_password_change: bool = True,
    ) -> ExaminerUserCreated:
        normalized_username = username.strip()
        existing = self._user_repo.find_examiner_by_username(self._db, normalized_username)
        if existing is not None:
            raise ConflictError("Examiner username already exists.")

        password_error = validate_password(password)
        if password_error:
            raise ConflictError(password_error)

        is_admin = self._user_repo.count_examiners(self._db) == 0
        created = self._user_repo.create_examiner(
            self._db,
            username=normalized_username,
            password_hash=hash_password(password),
            is_active=True,
            is_admin=is_admin,
        )
        self._db.commit()
        self._db.refresh(created)

        return ExaminerUserCreated(
            user_id=created.user_id,
            username=created.username or normalized_username,
            is_active=created.is_active,
            force_password_change=force_password_change,
            created_at=created.created_at,
        )

    def create(self, *, username: str, password: str, force_password_change: bool = True) -> ExaminerUserCreated:
        return self.create_examiner(
            username=username,
            password=password,
            force_password_change=force_password_change,
        )
