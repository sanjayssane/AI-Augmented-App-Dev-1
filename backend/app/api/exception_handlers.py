"""RFC 7807 exception handlers."""

from __future__ import annotations

import logging
from http import HTTPStatus

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.request_id import get_request_id
from app.schemas.errors import (
    AccountLockedError,
    AppError,
    FieldError,
    ProblemDetails,
    RateLimitExceededError,
)

logger = logging.getLogger(__name__)

_HTTP_TYPE_SUFFIXES = {
    404: "not-found",
    405: "method-not-allowed",
}


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


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Map framework HTTPExceptions (404 route, 405 method, ...) to problem+json."""
    status_code = exc.status_code
    try:
        title = HTTPStatus(status_code).phrase
    except ValueError:
        title = "Error"
    suffix = _HTTP_TYPE_SUFFIXES.get(
        status_code,
        title.lower().replace(" ", "-") if title != "Error" else "http-error",
    )
    problem = ProblemDetails(
        type=_problem_type(suffix),
        title=title,
        status=status_code,
        detail=str(exc.detail) if exc.detail else title,
        instance=str(request.url.path),
        request_id=get_request_id(),
    )
    headers = dict(exc.headers) if exc.headers else None
    return _problem_response(problem, headers=headers)


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Catch-all: return a problem+json 500 without leaking internals."""
    logger.exception(
        "Unhandled exception on %s %s",
        request.method,
        request.url.path,
        exc_info=exc,
    )
    problem = ProblemDetails(
        type=_problem_type("internal-error"),
        title="Internal Server Error",
        status=500,
        detail="An unexpected error occurred. Please try again later.",
        instance=str(request.url.path),
        request_id=get_request_id(),
    )
    return _problem_response(problem)
