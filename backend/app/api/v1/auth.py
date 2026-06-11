"""Authentication endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.openapi import SECURITY_SESSION, SECURITY_SESSION_CSRF, problem_responses
from app.core.auth import CsrfProtectedDep, CurrentUserDep
from app.core.cookies import clear_session_cookie, set_session_cookie
from app.core.deps import get_auth_service, get_csrf_service
from app.core.config import settings
from app.core.request_id import get_request_id
from app.schemas.auth import (
    CsrfTokenResponse,
    CurrentUserResponse,
    ExaminerLoginRequest,
    ExaminerLoginResponse,
    ExamineeEntryRequest,
    ExamineeSessionResource,
)
from app.schemas.common import SuccessResponse, success_envelope
from app.services.auth_service import AuthService
from app.services.csrf_service import CsrfService

router = APIRouter()


@router.get(
    "/auth/csrf",
    response_model=SuccessResponse[CsrfTokenResponse],
    summary="Issue a pre-login CSRF token",
    response_description="A short-lived CSRF token for unauthenticated flows.",
)
def get_csrf_token(
    csrf_service: Annotated[CsrfService, Depends(get_csrf_service)],
) -> SuccessResponse[CsrfTokenResponse]:
    """Issue a standalone CSRF token for pre-authentication flows.

    Use the returned token in the `X-CSRF-Token` header when calling the login
    and entry endpoints from a browser form. After authentication, prefer the
    session-bound token returned by `GET /auth/me`.
    """
    result = csrf_service.issue_token()
    return success_envelope(
        CsrfTokenResponse(csrf_token=result.token),
        request_id=get_request_id(),
    )


@router.post(
    "/auth/examiner/login",
    response_model=SuccessResponse[ExaminerLoginResponse],
    summary="Examiner login",
    response_description="Examiner profile; the session cookie is set on the response.",
    responses=problem_responses(
        400,
        401,
        423,
        overrides={
            401: {
                "description": "Invalid username or password.",
                "example": {
                    "type": "https://api.example.com/problems/invalid-credentials",
                    "title": "Invalid Credentials",
                    "status": 401,
                    "detail": "Invalid username or password",
                    "instance": "/api/v1/auth/examiner/login",
                    "request_id": "9f1b2c3d4e5f6a7b",
                },
            }
        },
    ),
)
def examiner_login(
    body: ExaminerLoginRequest,
    request: Request,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> SuccessResponse[ExaminerLoginResponse]:
    """Authenticate an examiner with username and password.

    On success an HttpOnly `session_id` cookie (1 hour TTL) is set on the
    response. After 5 failed attempts within 15 minutes the account is
    temporarily locked (423) and `locked_until` indicates when it reopens.
    """
    result = auth_service.examiner_login(
        username=body.username,
        password=body.password,
        client_ip=request.client.host if request.client else None,
    )
    set_session_cookie(response, result.session_token)
    return success_envelope(result.to_response(), request_id=get_request_id())


@router.post(
    "/auth/examinee/entry",
    response_model=SuccessResponse[ExamineeSessionResource],
    status_code=status.HTTP_200_OK,
    summary="Examinee entry (register or resume)",
    response_description="The active test session for the examinee (existing session resumed).",
    responses={
        201: {
            "model": SuccessResponse[ExamineeSessionResource],
            "description": "A new examinee account and test session were created.",
        },
        **problem_responses(
            400,
            403,
            409,
            429,
            503,
            overrides={
                403: {
                    "description": "Identity mismatch — the PRN exists but the name does not match.",
                    "example": {
                        "type": "https://api.example.com/problems/identity-mismatch",
                        "title": "Identity Mismatch",
                        "status": 403,
                        "detail": "The provided details do not match our records.",
                        "instance": "/api/v1/auth/examinee/entry",
                        "request_id": "9f1b2c3d4e5f6a7b",
                    },
                },
                409: {
                    "description": "This registration number has already completed the test (retakes disabled).",
                    "example": {
                        "type": "https://api.example.com/problems/exam-already-completed",
                        "title": "Exam Already Completed",
                        "status": 409,
                        "detail": "This registration number has already completed the test.",
                        "instance": "/api/v1/auth/examinee/entry",
                        "request_id": "9f1b2c3d4e5f6a7b",
                    },
                },
            },
        ),
    },
)
def examinee_entry(
    body: ExamineeEntryRequest,
    request: Request,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> SuccessResponse[ExamineeSessionResource]:
    """Register a new examinee or resume an in-progress test session.

    Identified by PRN (registration number) and name; privacy acknowledgement
    is mandatory. Returns **201** when a new account and session are created,
    **200** when an existing in-progress session is resumed. An HttpOnly
    `session_id` cookie (4 hour TTL) is set on the response. Registration is
    rate-limited per IP (429).
    """
    result = auth_service.examinee_entry(
        prn=body.prn,
        name=body.name,
        privacy_acknowledged=body.privacy_acknowledged,
        client_ip=request.client.host if request.client else None,
    )
    set_session_cookie(
        response,
        result.session_token,
        max_age=settings.examinee_session_ttl_seconds,
    )
    if result.created:
        response.status_code = status.HTTP_201_CREATED
    return success_envelope(result.session, request_id=get_request_id())


@router.post(
    "/auth/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out",
    response_description="Session invalidated; the session cookie is cleared.",
    responses=problem_responses(401, 403),
    openapi_extra=SECURITY_SESSION_CSRF,
)
def logout(
    response: Response,
    current_user: CurrentUserDep,
    _csrf: CsrfProtectedDep,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Response:
    """Invalidate the current session server-side and clear the session cookie.

    Requires an authenticated session and the `X-CSRF-Token` header.
    """
    auth_service.logout(
        session_token=current_user.session_token,
        user_id=current_user.user_id,
    )
    clear_session_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get(
    "/auth/me",
    response_model=SuccessResponse[CurrentUserResponse],
    summary="Get current user profile",
    response_description="Profile of the authenticated user, including the session CSRF token.",
    responses=problem_responses(401),
    openapi_extra=SECURITY_SESSION,
)
def get_current_user_profile(
    current_user: CurrentUserDep,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> SuccessResponse[CurrentUserResponse]:
    """Return the authenticated user's profile and session-bound CSRF token.

    Role-specific fields are populated: `username`/`is_admin` for examiners,
    `prn`/`name` for examinees. Use `csrf_token` in the `X-CSRF-Token` header
    on subsequent mutating requests.
    """
    profile = auth_service.get_current_user_profile(
        user_id=current_user.user_id,
        role=current_user.role,
        csrf_token=current_user.csrf_token,
    )
    return success_envelope(profile, request_id=get_request_id())
