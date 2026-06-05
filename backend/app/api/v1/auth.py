"""Authentication endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from app.core.auth import CurrentUserDep
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


@router.get("/auth/csrf", response_model=SuccessResponse[CsrfTokenResponse])
def get_csrf_token(
    csrf_service: Annotated[CsrfService, Depends(get_csrf_service)],
) -> SuccessResponse[CsrfTokenResponse]:
    result = csrf_service.issue_token()
    return success_envelope(
        CsrfTokenResponse(csrf_token=result.token),
        request_id=get_request_id(),
    )


@router.post("/auth/examiner/login", response_model=SuccessResponse[ExaminerLoginResponse])
def examiner_login(
    body: ExaminerLoginRequest,
    request: Request,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> SuccessResponse[ExaminerLoginResponse]:
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
)
def examinee_entry(
    body: ExamineeEntryRequest,
    request: Request,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> SuccessResponse[ExamineeSessionResource]:
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


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    current_user: CurrentUserDep,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Response:
    auth_service.logout(
        session_token=current_user.session_token,
        user_id=current_user.user_id,
    )
    clear_session_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/auth/me", response_model=SuccessResponse[CurrentUserResponse])
def get_current_user_profile(
    current_user: CurrentUserDep,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> SuccessResponse[CurrentUserResponse]:
    profile = auth_service.get_current_user_profile(
        user_id=current_user.user_id,
        role=current_user.role,
    )
    return success_envelope(profile, request_id=get_request_id())
