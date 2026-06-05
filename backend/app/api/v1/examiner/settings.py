"""Examiner platform settings endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.auth import ExaminerUserDep
from app.core.deps import get_settings_service
from app.core.request_id import get_request_id
from app.schemas.common import SuccessResponse, success_envelope
from app.schemas.examiner import PlatformSettingsOut, PlatformSettingsPatchRequest
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/examiner/settings")


@router.get("", response_model=SuccessResponse[PlatformSettingsOut])
def get_settings(
    _examiner: ExaminerUserDep,
    settings_service: Annotated[SettingsService, Depends(get_settings_service)],
) -> SuccessResponse[PlatformSettingsOut]:
    view = settings_service.get_settings()
    return success_envelope(
        PlatformSettingsOut(
            retention_days_completed=view.retention_days_completed,
            allow_examinee_retake=view.allow_examinee_retake,
            question_selection_mode=view.question_selection_mode,
        ),
        request_id=get_request_id(),
    )


@router.patch("", response_model=SuccessResponse[PlatformSettingsOut])
def patch_settings(
    body: PlatformSettingsPatchRequest,
    _examiner: ExaminerUserDep,
    settings_service: Annotated[SettingsService, Depends(get_settings_service)],
) -> SuccessResponse[PlatformSettingsOut]:
    view = settings_service.patch_settings(
        retention_days_completed=body.retention_days_completed,
        allow_examinee_retake=body.allow_examinee_retake,
        question_selection_mode=body.question_selection_mode,
    )
    return success_envelope(
        PlatformSettingsOut(
            retention_days_completed=view.retention_days_completed,
            allow_examinee_retake=view.allow_examinee_retake,
            question_selection_mode=view.question_selection_mode,
        ),
        request_id=get_request_id(),
    )
