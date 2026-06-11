"""Reusable OpenAPI documentation helpers.

Centralises RFC 7807 ``application/problem+json`` error response definitions
and per-operation security markers so route decorators stay concise and the
generated Swagger / ReDoc documentation is consistent across endpoints.
"""

from __future__ import annotations

from typing import Any

PROBLEM_CONTENT_TYPE = "application/problem+json"
PROBLEM_SCHEMA_REF = {"$ref": "#/components/schemas/ProblemDetails"}

# Security scheme names registered in app.main's custom OpenAPI generator.
SESSION_COOKIE_SCHEME = "sessionCookie"
CSRF_HEADER_SCHEME = "csrfToken"

# Pass as ``openapi_extra`` on routes that only require an authenticated session.
SECURITY_SESSION: dict[str, Any] = {"security": [{SESSION_COOKIE_SCHEME: []}]}

# Pass as ``openapi_extra`` on mutating routes that also require the X-CSRF-Token header.
SECURITY_SESSION_CSRF: dict[str, Any] = {
    "security": [{SESSION_COOKIE_SCHEME: [], CSRF_HEADER_SCHEME: []}]
}

_EXAMPLE_REQUEST_ID = "9f1b2c3d4e5f6a7b"
_EXAMPLE_TYPE_BASE = "https://api.example.com/problems"


def _example(
    status: int,
    *,
    title: str,
    type_suffix: str,
    detail: str,
    **extra: Any,
) -> dict[str, Any]:
    return {
        "type": f"{_EXAMPLE_TYPE_BASE}/{type_suffix}",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": "/api/v1/...",
        "request_id": _EXAMPLE_REQUEST_ID,
        **extra,
    }


# Default catalogue of error responses produced by the exception handlers in
# app.api.exception_handlers (validation errors are returned as 400, not 422).
_PROBLEM_CATALOGUE: dict[int, dict[str, Any]] = {
    400: {
        "description": "Validation error — one or more request fields are invalid.",
        "example": _example(
            400,
            title="Validation Error",
            type_suffix="validation-error",
            detail="One or more fields failed validation.",
            errors=[{"field": "username", "message": "String should have at least 1 character"}],
        ),
    },
    401: {
        "description": "Unauthenticated — missing or expired session cookie.",
        "example": _example(
            401,
            title="Unauthenticated",
            type_suffix="unauthenticated",
            detail="Authentication required.",
        ),
    },
    403: {
        "description": "Forbidden — insufficient role or CSRF token validation failed.",
        "example": _example(
            403,
            title="Forbidden",
            type_suffix="forbidden",
            detail="You do not have permission to perform this action.",
        ),
    },
    404: {
        "description": "The requested resource was not found.",
        "example": _example(
            404,
            title="Not Found",
            type_suffix="not-found",
            detail="The requested resource was not found.",
        ),
    },
    409: {
        "description": "Conflict — the resource state prevents this operation.",
        "example": _example(
            409,
            title="Conflict",
            type_suffix="conflict",
            detail="The resource was modified by another request.",
        ),
    },
    423: {
        "description": "Account locked after too many failed login attempts.",
        "example": _example(
            423,
            title="Account Locked",
            type_suffix="locked",
            detail="This account is temporarily locked due to too many failed login attempts.",
            locked_until="2026-01-01T12:30:00Z",
        ),
    },
    429: {
        "description": "Rate limit exceeded — retry after the indicated delay.",
        "example": _example(
            429,
            title="Rate Limit Exceeded",
            type_suffix="rate-limit-exceeded",
            detail="Too many requests. Please try again later.",
        ),
    },
    503: {
        "description": "Service unavailable — a required dependency or resource is not ready.",
        "example": _example(
            503,
            title="Insufficient Question Bank",
            type_suffix="service-unavailable",
            detail="The question bank does not have enough active questions.",
        ),
    },
}


def problem_responses(
    *status_codes: int,
    overrides: dict[int, dict[str, Any]] | None = None,
) -> dict[int | str, dict[str, Any]]:
    """Build a FastAPI ``responses=`` mapping of RFC 7807 error documentation.

    ``overrides`` may replace the default ``description`` and/or ``example``
    for a given status code, e.g. to document a 401 as invalid credentials
    rather than a missing session.
    """
    responses: dict[int | str, dict[str, Any]] = {}
    for code in status_codes:
        entry = dict(_PROBLEM_CATALOGUE[code])
        if overrides and code in overrides:
            entry = {**entry, **overrides[code]}
        responses[code] = {
            "description": entry["description"],
            "content": {
                PROBLEM_CONTENT_TYPE: {
                    "schema": PROBLEM_SCHEMA_REF,
                    "example": entry["example"],
                }
            },
        }
    return responses
