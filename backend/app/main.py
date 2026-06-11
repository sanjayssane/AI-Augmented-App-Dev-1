"""FastAPI application entry point."""

from typing import Any

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.exception_handlers import (
    app_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_error_handler,
)
from app.api.middleware import RequestIdMiddleware, SecurityHeadersMiddleware
from app.api.openapi import CSRF_HEADER_SCHEME, SESSION_COOKIE_SCHEME
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.schemas.errors import AppError, ProblemDetails

API_DESCRIPTION = """
Role-based REST API for the MCQ Online Test Platform: examiners manage a
question bank and review results, while examinees take a 50-question
multiple-choice test.

## Roles

| Role | How authenticated | Capabilities |
|------|-------------------|--------------|
| **Examinee** | `POST /auth/examinee/entry` (PRN + name) | Take the test, review answers, export own data |
| **Examiner** | `POST /auth/examiner/login` (username + password) | Manage questions, view session results, read settings |
| **Admin examiner** | Examiner login with admin flag | Additionally create examiners, update settings, request GDPR erasure |

## Authentication

Authentication uses an **opaque server-side session** stored in Redis and
delivered via an HttpOnly `session_id` cookie (path `/api/v1`,
`SameSite=strict`). There are no bearer tokens. Cookies are set by the login
and entry endpoints and cleared by `POST /auth/logout`.

## CSRF protection

All mutating endpoints (POST/PUT/PATCH/DELETE) on authenticated routes
require the `X-CSRF-Token` header. The session-bound token is returned by
`GET /auth/me`; a pre-login token for the login forms is available from
`GET /auth/csrf`.

## Response conventions

- **Success** responses wrap the payload in an envelope:
  `{ "data": ..., "meta": { "request_id": "..." } }`.
- **Errors** are returned as RFC 7807 problem details with content type
  `application/problem+json` (see the `ProblemDetails` schema). Validation
  failures return **400** with a field-level `errors` array.
- Every response carries an `X-Request-Id` header that matches
  `meta.request_id`, for log correlation.
- File downloads (data export, CSV export) bypass the envelope and return
  raw content with a `Content-Disposition: attachment` header.
""".strip()

OPENAPI_TAGS = [
    {
        "name": "health",
        "description": "Liveness and readiness probes for orchestration and monitoring. No authentication required.",
    },
    {
        "name": "auth",
        "description": "Session lifecycle: examiner login, examinee entry/registration, logout, current-user profile, and CSRF token issuance.",
    },
    {
        "name": "examinee",
        "description": "Examinee test-taking flow: resume the active session, fetch questions by position, save answers, submit for scoring, review results, and export personal data (GDPR). Requires an examinee session.",
    },
    {
        "name": "examiner-questions",
        "description": "Question bank management: list, create, edit, and soft-delete multiple-choice questions. Requires an examiner session.",
    },
    {
        "name": "examiner-sessions",
        "description": "Test session results: paginated listings, per-question detail, and CSV export. Requires an examiner session.",
    },
    {
        "name": "examiner-users",
        "description": "User administration: create examiner accounts and request GDPR erasure of examinee data. Requires an admin examiner session.",
    },
    {
        "name": "examiner-settings",
        "description": "Platform settings: data retention, retake policy, and question selection mode. Reads require an examiner session; updates require an admin examiner session.",
    },
]

app = FastAPI(
    title="MCQ Online Test Platform API",
    version="0.1.0",
    description=API_DESCRIPTION,
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_tags=OPENAPI_TAGS,
)


def custom_openapi() -> dict[str, Any]:
    """Generate the OpenAPI schema with security schemes and shared error models."""
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=OPENAPI_TAGS,
    )

    components = schema.setdefault("components", {})
    components.setdefault("securitySchemes", {})[SESSION_COOKIE_SCHEME] = {
        "type": "apiKey",
        "in": "cookie",
        "name": settings.session_cookie_name,
        "description": (
            "Opaque server-side session token issued by the login/entry endpoints "
            "as an HttpOnly cookie. Examiner sessions last 1 hour, examinee "
            "sessions 4 hours by default."
        ),
    }
    components["securitySchemes"][CSRF_HEADER_SCHEME] = {
        "type": "apiKey",
        "in": "header",
        "name": "X-CSRF-Token",
        "description": (
            "Session-bound CSRF token required on mutating requests. "
            "Obtain it from GET /auth/me (or GET /auth/csrf before login)."
        ),
    }

    # Register the RFC 7807 ProblemDetails model so error responses defined in
    # app.api.openapi can reference it even though no route returns it directly.
    schemas = components.setdefault("schemas", {})
    problem_schema = ProblemDetails.model_json_schema(
        ref_template="#/components/schemas/{model}"
    )
    for name, definition in problem_schema.pop("$defs", {}).items():
        schemas.setdefault(name, definition)
    schemas.setdefault("ProblemDetails", problem_schema)

    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi  # type: ignore[method-assign]

app.add_middleware(RequestIdMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(api_v1_router, prefix="/api/v1")
