"""Examiner administration endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.auth import ExaminerUserDep
from app.core.deps import get_user_admin_service
from app.core.request_id import get_request_id
from app.schemas.common import SuccessResponse, success_envelope
from app.schemas.examiner import CreateExaminerRequest, EraseExamineeResponse, ExaminerUserOut
from app.services.user_admin_service import UserAdminService

router = APIRouter(prefix="/examiner/users")


@router.post("/examiners", status_code=status.HTTP_201_CREATED, response_model=SuccessResponse[ExaminerUserOut])
def create_examiner(
    body: CreateExaminerRequest,
    _examiner: ExaminerUserDep,
    user_admin_service: Annotated[UserAdminService, Depends(get_user_admin_service)],
) -> SuccessResponse[ExaminerUserOut]:
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


@router.post("/examinees/{user_id}/erase", status_code=status.HTTP_202_ACCEPTED, response_model=SuccessResponse[EraseExamineeResponse])
def erase_examinee(
    user_id: uuid.UUID,
    _examiner: ExaminerUserDep,
) -> SuccessResponse[EraseExamineeResponse]:
    return success_envelope(
        EraseExamineeResponse(user_id=user_id),
        request_id=get_request_id(),
    )
