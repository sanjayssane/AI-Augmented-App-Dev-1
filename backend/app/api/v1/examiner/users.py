"""Examiner administration endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.openapi import SECURITY_SESSION_CSRF, problem_responses
from app.core.auth import AdminExaminerDep, CsrfProtectedDep
from app.core.deps import get_gdpr_service, get_user_admin_service
from app.core.request_id import get_request_id
from app.schemas.common import SuccessResponse, success_envelope
from app.schemas.examiner import CreateExaminerRequest, EraseExamineeResponse, ExaminerUserOut
from app.services.gdpr_service import GdprService
from app.services.user_admin_service import UserAdminService

router = APIRouter(prefix="/examiner/users")


@router.post(
    "/examiners",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[ExaminerUserOut],
    summary="Create an examiner account",
    response_description="The newly created examiner account.",
    responses=problem_responses(
        400,
        401,
        403,
        409,
        overrides={409: {"description": "An examiner with this username already exists."}},
    ),
    openapi_extra=SECURITY_SESSION_CSRF,
)
def create_examiner(
    body: CreateExaminerRequest,
    admin: AdminExaminerDep,
    _csrf: CsrfProtectedDep,
    user_admin_service: Annotated[UserAdminService, Depends(get_user_admin_service)],
) -> SuccessResponse[ExaminerUserOut]:
    """Create a new examiner account (admin only).

    The password must satisfy the platform policy (minimum 12 characters).
    By default the new examiner must change their password on first login.
    Requires an admin examiner session and the `X-CSRF-Token` header.
    """
    created = user_admin_service.create_examiner(
        username=body.username,
        password=body.password,
        force_password_change=body.force_password_change,
    )
    return success_envelope(
        ExaminerUserOut(
            user_id=created.user_id,
            username=created.username,
            is_active=created.is_active,
            force_password_change=created.force_password_change,
            created_at=created.created_at,
        ),
        request_id=get_request_id(),
    )


@router.post(
    "/examinees/{user_id}/erase",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=SuccessResponse[EraseExamineeResponse],
    summary="Request GDPR erasure of an examinee",
    response_description="Erasure job accepted for asynchronous processing.",
    responses=problem_responses(401, 403, 404),
    openapi_extra=SECURITY_SESSION_CSRF,
)
def erase_examinee(
    user_id: uuid.UUID,
    admin: AdminExaminerDep,
    _csrf: CsrfProtectedDep,
    gdpr_service: Annotated[GdprService, Depends(get_gdpr_service)],
) -> SuccessResponse[EraseExamineeResponse]:
    """Request asynchronous erasure of an examinee's personal data (GDPR Art. 17).

    Returns **202** with a `job_id`; the erasure is processed in the
    background. Requires an admin examiner session and the `X-CSRF-Token`
    header.
    """
    job_id = gdpr_service.request_erasure(
        examinee_user_id=user_id,
        operator_user_id=admin.user_id,
    )
    return success_envelope(
        EraseExamineeResponse(user_id=user_id, job_id=job_id),
        request_id=get_request_id(),
    )
