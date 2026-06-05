"""RFC 7807 exception handlers."""

from __future__ import annotations

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.request_id import get_request_id
from app.schemas.errors import (
    AccountLockedError,
    AppError,
    FieldError,
    ProblemDetails,
    RateLimitExceededError,
)


def _problem_type(suffix: str) -> str:
    return f"{settings.problem_type_base_url}/{suffix}"


def _problem_response(
    problem: ProblemDetails,
    *,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=problem.status,
        content=problem.model_dump(mode="json"),
        media_type="application/problem+json",
        headers=headers,
    )


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    problem = ProblemDetails(
        type=_problem_type(exc.type_suffix),
        title=exc.title,
        status=exc.status_code,
        detail=exc.detail,
        instance=str(_request.url.path),
        request_id=get_request_id(),
    )
    headers: dict[str, str] | None = None
    if isinstance(exc, AccountLockedError):
        problem.locked_until = exc.locked_until
    if isinstance(exc, RateLimitExceededError) and exc.retry_after is not None:
        headers = {"Retry-After": str(exc.retry_after)}
    return _problem_response(problem, headers=headers)


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors = [
        FieldError(
            field=".".join(str(part) for part in err["loc"] if part != "body"),
            message=err["msg"],
        )
        for err in exc.errors()
    ]
    problem = ProblemDetails(
        type=_problem_type("validation-error"),
        title="Validation Error",
        status=400,
        detail="One or more fields failed validation.",
        instance=str(request.url.path),
        request_id=get_request_id(),
        errors=errors,
    )
    return _problem_response(problem)
