"""FastAPI dependency injection."""

from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from redis import Redis
from sqlalchemy.orm import Session

from app.core.database import get_db as _get_db
from app.core.redis import get_redis_client
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.erasure_job_repository import ErasureJobRepository
from app.repositories.platform_settings_repository import PlatformSettingsRepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.question_version_repository import QuestionVersionRepository
from app.repositories.response_repository import ResponseRepository
from app.repositories.redis.submit_idempotency_store import SubmitIdempotencyStore
from app.repositories.test_session_repository import TestSessionRepository
from app.repositories.redis.rate_limit_store import RateLimitStore
from app.repositories.redis.lockout_store import LockoutStore
from app.repositories.redis.session_store import SessionStore
from app.repositories.redis.csrf_store import CsrfStore
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.csrf_service import CsrfService
from app.services.gdpr_service import GdprService
from app.services.question_service import QuestionService
from app.services.results_service import ResultsService
from app.services.scoring_service import ScoringService
from app.services.settings_service import SettingsService
from app.services.test_session_service import TestSessionService
from app.services.user_admin_service import UserAdminService


def get_db() -> Generator[Session, None, None]:
    yield from _get_db()


def get_redis() -> Redis:
    return get_redis_client()


def get_user_repository() -> UserRepository:
    return UserRepository()


def get_session_store(redis: Annotated[Redis, Depends(get_redis)]) -> SessionStore:
    return SessionStore(redis)


def get_lockout_store(redis: Annotated[Redis, Depends(get_redis)]) -> LockoutStore:
    return LockoutStore(redis)


def get_rate_limit_store(redis: Annotated[Redis, Depends(get_redis)]) -> RateLimitStore:
    return RateLimitStore(redis)


def get_csrf_store(redis: Annotated[Redis, Depends(get_redis)]) -> CsrfStore:
    return CsrfStore(redis)


def get_submit_idempotency_store(
    redis: Annotated[Redis, Depends(get_redis)],
) -> SubmitIdempotencyStore:
    return SubmitIdempotencyStore(redis)


def get_audit_log_repository() -> AuditLogRepository:
    return AuditLogRepository()


def get_erasure_job_repository() -> ErasureJobRepository:
    return ErasureJobRepository()


def get_test_session_repository() -> TestSessionRepository:
    return TestSessionRepository()


def get_question_repository() -> QuestionRepository:
    return QuestionRepository()


def get_question_version_repository() -> QuestionVersionRepository:
    return QuestionVersionRepository()


def get_platform_settings_repository() -> PlatformSettingsRepository:
    return PlatformSettingsRepository()


def get_response_repository() -> ResponseRepository:
    return ResponseRepository()


def get_audit_service(
    db: Annotated[Session, Depends(get_db)],
    audit_repo: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> AuditService:
    return AuditService(db=db, audit_repo=audit_repo)


def get_auth_service(
    db: Annotated[Session, Depends(get_db)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    session_store: Annotated[SessionStore, Depends(get_session_store)],
    lockout_store: Annotated[LockoutStore, Depends(get_lockout_store)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    test_session_repo: Annotated[TestSessionRepository, Depends(get_test_session_repository)],
    question_repo: Annotated[QuestionRepository, Depends(get_question_repository)],
    platform_settings_repo: Annotated[
        PlatformSettingsRepository, Depends(get_platform_settings_repository)
    ],
    rate_limit_store: Annotated[RateLimitStore, Depends(get_rate_limit_store)],
    response_repo: Annotated[ResponseRepository, Depends(get_response_repository)],
) -> AuthService:
    return AuthService(
        db=db,
        user_repo=user_repo,
        session_store=session_store,
        lockout_store=lockout_store,
        audit_service=audit_service,
        test_session_repo=test_session_repo,
        question_repo=question_repo,
        platform_settings_repo=platform_settings_repo,
        rate_limit_store=rate_limit_store,
        response_repo=response_repo,
    )


def get_csrf_service(
    csrf_store: Annotated[CsrfStore, Depends(get_csrf_store)],
) -> CsrfService:
    return CsrfService(csrf_store=csrf_store)


def get_test_session_service(
    db: Annotated[Session, Depends(get_db)],
    test_session_repo: Annotated[TestSessionRepository, Depends(get_test_session_repository)],
    response_repo: Annotated[ResponseRepository, Depends(get_response_repository)],
) -> TestSessionService:
    return TestSessionService(
        db=db,
        test_session_repo=test_session_repo,
        response_repo=response_repo,
    )


def get_scoring_service(
    db: Annotated[Session, Depends(get_db)],
    test_session_repo: Annotated[TestSessionRepository, Depends(get_test_session_repository)],
    response_repo: Annotated[ResponseRepository, Depends(get_response_repository)],
    question_version_repo: Annotated[QuestionVersionRepository, Depends(get_question_version_repository)],
    submit_idempotency_store: Annotated[
        SubmitIdempotencyStore,
        Depends(get_submit_idempotency_store),
    ],
) -> ScoringService:
    return ScoringService(
        db=db,
        test_session_repo=test_session_repo,
        response_repo=response_repo,
        question_version_repo=question_version_repo,
        submit_idempotency_store=submit_idempotency_store,
    )


def get_gdpr_service(
    db: Annotated[Session, Depends(get_db)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    erasure_job_repo: Annotated[ErasureJobRepository, Depends(get_erasure_job_repository)],
) -> GdprService:
    return GdprService(
        db=db,
        user_repo=user_repo,
        erasure_job_repo=erasure_job_repo,
    )


def get_question_service(
    db: Annotated[Session, Depends(get_db)],
    question_repo: Annotated[QuestionRepository, Depends(get_question_repository)],
    question_version_repo: Annotated[QuestionVersionRepository, Depends(get_question_version_repository)],
) -> QuestionService:
    return QuestionService(
        db=db,
        question_repo=question_repo,
        question_version_repo=question_version_repo,
    )


def get_results_service(
    db: Annotated[Session, Depends(get_db)],
    session_repo: Annotated[TestSessionRepository, Depends(get_test_session_repository)],
) -> ResultsService:
    return ResultsService(db=db, session_repo=session_repo)


def get_settings_service(
    db: Annotated[Session, Depends(get_db)],
    settings_repo: Annotated[PlatformSettingsRepository, Depends(get_platform_settings_repository)],
) -> SettingsService:
    return SettingsService(db=db, settings_repo=settings_repo)


def get_user_admin_service(
    db: Annotated[Session, Depends(get_db)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserAdminService:
    return UserAdminService(db=db, user_repo=user_repo)
