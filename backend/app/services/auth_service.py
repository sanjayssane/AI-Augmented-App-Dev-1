"""Authentication use cases."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.encryption import decrypt_field, prn_lookup_hash
from app.core.passwords import verify_password
from app.domain.question_selection import SESSION_QUESTION_COUNT, select_questions
from app.domain.session_rules import session_expires_at
from app.domain.validation import names_match
from app.models.enums import SelectionMode, SessionStatus, UserRole
from app.models.session import TestSession
from app.models.user import User
from app.repositories.platform_settings_repository import PlatformSettingsRepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.redis.lockout_store import LockoutStore
from app.repositories.redis.rate_limit_store import RateLimitStore
from app.repositories.redis.session_store import SessionStore
from app.repositories.response_repository import ResponseRepository
from app.repositories.test_session_repository import TestSessionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import CurrentUserResponse, ExaminerLoginResponse, ExamineeSessionResource
from app.schemas.errors import (
    AccountLockedError,
    ExamAlreadyCompletedError,
    IdentityMismatchError,
    InsufficientQuestionBankError,
    InvalidCredentialsError,
    RateLimitExceededError,
    UnauthenticatedError,
)
from app.services.audit_service import AuditService


@dataclass
class ExaminerLoginResult:
    user_id: uuid.UUID
    username: str
    must_change_password: bool
    session_token: str

    def to_response(self) -> ExaminerLoginResponse:
        return ExaminerLoginResponse(
            user_id=self.user_id,
            username=self.username,
            must_change_password=self.must_change_password,
        )


@dataclass
class ExamineeEntryResult:
    session: ExamineeSessionResource
    session_token: str
    created: bool


class AuthService:
    def __init__(
        self,
        db: Session,
        user_repo: UserRepository,
        session_store: SessionStore,
        lockout_store: LockoutStore,
        audit_service: AuditService,
        test_session_repo: TestSessionRepository,
        question_repo: QuestionRepository,
        platform_settings_repo: PlatformSettingsRepository,
        rate_limit_store: RateLimitStore,
        response_repo: ResponseRepository,
    ) -> None:
        self._db = db
        self._user_repo = user_repo
        self._session_store = session_store
        self._lockout_store = lockout_store
        self._audit_service = audit_service
        self._test_session_repo = test_session_repo
        self._question_repo = question_repo
        self._platform_settings_repo = platform_settings_repo
        self._rate_limit_store = rate_limit_store
        self._response_repo = response_repo

    def examiner_login(
        self,
        *,
        username: str,
        password: str,
        client_ip: str | None,
    ) -> ExaminerLoginResult:
        normalized_username = username.strip()

        locked_until = self._lockout_store.is_locked(normalized_username)
        if locked_until is not None:
            raise AccountLockedError(locked_until)

        user = self._user_repo.find_examiner_by_username(self._db, normalized_username)
        password_hash = user.password_hash if user else ""
        credentials_valid = (
            user is not None
            and user.is_active
            and password_hash
            and verify_password(password, password_hash)
        )

        if not credentials_valid:
            lockout_state = self._lockout_store.record_failure(normalized_username)
            self._audit_service.log_login_failed(
                user.user_id if user else None,
                client_ip,
            )
            if lockout_state.locked_until is not None:
                self._audit_service.log_account_locked(
                    user.user_id if user else None,
                    client_ip,
                )
                raise AccountLockedError(lockout_state.locked_until)
            raise InvalidCredentialsError()

        assert user is not None
        self._lockout_store.clear(normalized_username)
        self._session_store.invalidate_all_for_user(user.user_id)
        session_token = self._session_store.create_session(user.user_id, UserRole.EXAMINER)
        self._audit_service.log_login_success(user.user_id, client_ip)

        return ExaminerLoginResult(
            user_id=user.user_id,
            username=user.username or normalized_username,
            must_change_password=False,
            session_token=session_token,
        )

    def examinee_entry(
        self,
        *,
        prn: str,
        name: str,
        privacy_acknowledged: bool,
        client_ip: str | None,
    ) -> ExamineeEntryResult:
        if not privacy_acknowledged:
            raise IdentityMismatchError()

        rate_limit_key = f"auth:examinee_entry:{client_ip or 'unknown'}"
        allowed, retry_after = self._rate_limit_store.check_and_increment(
            rate_limit_key,
            max_requests=settings.registration_rate_limit_max,
            window_seconds=settings.registration_rate_limit_window_seconds,
        )
        if not allowed:
            raise RateLimitExceededError(retry_after=retry_after)

        user = self._user_repo.find_by_prn_hash(self._db, prn_lookup_hash(prn))

        if user is None:
            user = self._user_repo.create_examinee(
                self._db,
                prn=prn,
                name=name,
                privacy_acknowledged_at=datetime.now(UTC),
            )
            return self._create_examinee_session(user, created=True)

        if not user.is_active:
            raise IdentityMismatchError()

        self._ensure_examinee_name_matches(user, name)
        if user.privacy_acknowledged_at is None and privacy_acknowledged:
            user.privacy_acknowledged_at = datetime.now(UTC)

        active_session = self._test_session_repo.find_active_for_user(self._db, user.user_id)
        if active_session is not None:
            session_token = self._session_store.create_session(user.user_id, UserRole.EXAMINEE)
            return ExamineeEntryResult(
                session=self._build_session_resource(active_session),
                session_token=session_token,
                created=False,
            )

        latest_session = self._test_session_repo.find_latest_for_user(self._db, user.user_id)
        if latest_session and latest_session.status == SessionStatus.COMPLETED:
            if not self._allow_examinee_retake():
                raise ExamAlreadyCompletedError()
            return self._create_examinee_session(user, created=True)

        return self._create_examinee_session(user, created=True)

    def logout(self, *, session_token: str, user_id: uuid.UUID) -> None:
        self._session_store.delete_session(session_token, user_id)

    def get_current_user_profile(
        self,
        *,
        user_id: uuid.UUID,
        role: UserRole,
        csrf_token: str,
    ) -> CurrentUserResponse:
        user = self._user_repo.find_by_id(self._db, user_id)
        if user is None:
            raise UnauthenticatedError()

        if role == UserRole.EXAMINEE:
            if user.prn_ciphertext is None or user.name_ciphertext is None:
                raise UnauthenticatedError()
            return CurrentUserResponse(
                user_id=user.user_id,
                role=user.role,
                csrf_token=csrf_token,
                prn=decrypt_field(user.prn_ciphertext),
                name=decrypt_field(user.name_ciphertext),
                is_admin=False,
            )

        return CurrentUserResponse(
            user_id=user.user_id,
            role=user.role,
            csrf_token=csrf_token,
            username=user.username,
            is_admin=user.is_admin,
        )

    def _allow_examinee_retake(self) -> bool:
        value = self._platform_settings_repo.get_value(self._db, "allow_examinee_retake")
        if isinstance(value, bool):
            return value
        if isinstance(value, dict):
            nested = value.get("value")
            if isinstance(nested, bool):
                return nested
        return False

    def _selection_mode(self) -> SelectionMode:
        value = self._platform_settings_repo.get_value(self._db, "question_selection_mode")
        selected = value
        if isinstance(value, dict):
            selected = value.get("value")
        if isinstance(selected, str):
            try:
                return SelectionMode(selected)
            except ValueError:
                return SelectionMode.FIXED_ORDER
        return SelectionMode.FIXED_ORDER

    def _create_examinee_session(self, user: User, *, created: bool) -> ExamineeEntryResult:
        active_question_count = self._question_repo.count_active(self._db)
        if active_question_count < settings.min_active_questions:
            raise InsufficientQuestionBankError()

        mode = self._selection_mode()
        questions = self._question_repo.list_active_for_selection(
            self._db,
            limit=max(active_question_count, SESSION_QUESTION_COUNT),
        )
        try:
            selected_questions = select_questions(questions, mode)
        except ValueError as exc:
            # Bank shrank between the count check and selection; surface as 503.
            raise InsufficientQuestionBankError() from exc

        now = datetime.now(UTC)
        expires_at = session_expires_at(now)

        test_session = self._test_session_repo.create_with_questions_and_responses(
            self._db,
            user_id=user.user_id,
            selection_mode=mode,
            start_time=now,
            expires_at=expires_at,
            questions=selected_questions,
        )
        self._db.commit()
        session_token = self._session_store.create_session(user.user_id, UserRole.EXAMINEE)

        return ExamineeEntryResult(
            session=self._build_session_resource(test_session),
            session_token=session_token,
            created=created,
        )

    def _build_session_resource(self, test_session: TestSession) -> ExamineeSessionResource:
        answered_count = self._response_repo.count_answered(
            self._db,
            session_id=test_session.session_id,
        )
        return ExamineeSessionResource(
            session_id=test_session.session_id,
            status=test_session.status,
            total_questions=SESSION_QUESTION_COUNT,
            answered_count=answered_count,
            current_position=1,
            started_at=test_session.start_time,
            expires_at=test_session.expires_at,
        )

    def _ensure_examinee_name_matches(self, user: User, provided_name: str) -> None:
        if user.name_ciphertext is None:
            raise IdentityMismatchError()
        stored_name = decrypt_field(user.name_ciphertext)
        if not names_match(stored_name, provided_name):
            raise IdentityMismatchError()
