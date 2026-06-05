"""Domain errors and RFC 7807 problem detail models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class FieldError(BaseModel):
    field: str
    message: str


class ProblemDetails(BaseModel):
    type: str
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None
    request_id: str | None = None
    errors: list[FieldError] | None = None
    locked_until: datetime | None = None

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        data = super().model_dump(**kwargs)
        return {k: v for k, v in data.items() if v is not None}


class AppError(Exception):
    """Base application error mapped to RFC 7807."""

    status_code: int = 500
    title: str = "Internal Server Error"
    type_suffix: str = "internal-error"
    detail: str = "An unexpected error occurred."

    def __init__(self, detail: str | None = None) -> None:
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class InvalidCredentialsError(AppError):
    status_code = 401
    title = "Invalid Credentials"
    type_suffix = "invalid-credentials"
    detail = "Invalid username or password"


class AccountLockedError(AppError):
    status_code = 423
    title = "Account Locked"
    type_suffix = "locked"
    detail = "This account is temporarily locked due to too many failed login attempts."

    def __init__(self, locked_until: datetime) -> None:
        self.locked_until = locked_until
        super().__init__()


class RateLimitExceededError(AppError):
    status_code = 429
    title = "Rate Limit Exceeded"
    type_suffix = "rate-limit-exceeded"
    detail = "Too many requests. Please try again later."

    def __init__(self, retry_after: int | None = None) -> None:
        self.retry_after = retry_after
        super().__init__()


class UnauthenticatedError(AppError):
    status_code = 401
    title = "Unauthenticated"
    type_suffix = "unauthenticated"
    detail = "Authentication required."


class ForbiddenError(AppError):
    status_code = 403
    title = "Forbidden"
    type_suffix = "forbidden"
    detail = "You do not have permission to perform this action."


class NotFoundError(AppError):
    status_code = 404
    title = "Not Found"
    type_suffix = "not-found"
    detail = "The requested resource was not found."


class IdentityMismatchError(AppError):
    status_code = 403
    title = "Identity Mismatch"
    type_suffix = "identity-mismatch"
    detail = "The provided details do not match our records."


class ExamAlreadyCompletedError(AppError):
    status_code = 409
    title = "Exam Already Completed"
    type_suffix = "exam-already-completed"
    detail = "This registration number has already completed the test."


class SessionNotFoundError(AppError):
    status_code = 404
    title = "Session Not Found"
    type_suffix = "session-not-found"
    detail = "No active session was found."


class InsufficientQuestionBankError(AppError):
    status_code = 503
    title = "Insufficient Question Bank"
    type_suffix = "service-unavailable"
    detail = "The question bank does not have enough active questions."


class BankBelowMinimumError(AppError):
    status_code = 409
    title = "Bank Below Minimum"
    type_suffix = "conflict"
    detail = "This operation would reduce the active question bank below the minimum."

    def __init__(self, active_count: int | None = None) -> None:
        self.active_count = active_count
        if active_count is not None:
            super().__init__(f"Active question count would be {active_count}, below minimum.")
        else:
            super().__init__()


class ConflictError(AppError):
    status_code = 409
    title = "Conflict"
    type_suffix = "conflict"
    detail = "The resource was modified by another request."


class CsrfValidationError(AppError):
    status_code = 403
    title = "Forbidden"
    type_suffix = "forbidden"
    detail = "CSRF token validation failed."
