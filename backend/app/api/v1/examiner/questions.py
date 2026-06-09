"""Examiner question bank endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.auth import CsrfProtectedDep, ExaminerUserDep
from app.core.deps import get_question_service
from app.core.request_id import get_request_id
from app.schemas.common import SuccessResponse, success_envelope
from app.schemas.examiner import (
    QuestionCreateRequest,
    QuestionListData,
    QuestionOut,
    QuestionPatchRequest,
)
from app.services.question_service import QuestionPayload, QuestionService

router = APIRouter(prefix="/examiner/questions")


def _to_out(row) -> QuestionOut:
    return QuestionOut(
        question_id=row.question_id,
        question_text=row.question_text,
        option_a=row.option_a,
        option_b=row.option_b,
        option_c=row.option_c,
        option_d=row.option_d,
        correct_option=row.correct_option,
        question_version=row.question_version,
        is_deleted=row.is_deleted,
        updated_at=row.updated_at,
    )


@router.get("", response_model=SuccessResponse[QuestionListData])
def list_questions(
    _examiner: ExaminerUserDep,
    question_service: Annotated[QuestionService, Depends(get_question_service)],
    limit: int = Query(default=50, ge=1, le=100),
    cursor: uuid.UUID | None = Query(default=None),
    include_deleted: bool = Query(default=False),
) -> SuccessResponse[QuestionListData]:
    rows, next_cursor, active_count = question_service.list_questions(
        limit=limit,
        cursor=cursor,
        include_deleted=include_deleted,
    )
    return success_envelope(
        QuestionListData(items=[_to_out(r) for r in rows], next_cursor=next_cursor, active_count=active_count),
        request_id=get_request_id(),
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SuccessResponse[QuestionOut])
def create_question(
    body: QuestionCreateRequest,
    examiner: ExaminerUserDep,
    _csrf: CsrfProtectedDep,
    question_service: Annotated[QuestionService, Depends(get_question_service)],
) -> SuccessResponse[QuestionOut]:
    created = question_service.create_question(
        payload=QuestionPayload(**body.model_dump()),
        created_by=examiner.user_id,
    )
    return success_envelope(_to_out(created), request_id=get_request_id())


@router.patch("/{question_id}", response_model=SuccessResponse[QuestionOut])
def patch_question(
    question_id: uuid.UUID,
    body: QuestionPatchRequest,
    examiner: ExaminerUserDep,
    _csrf: CsrfProtectedDep,
    question_service: Annotated[QuestionService, Depends(get_question_service)],
) -> SuccessResponse[QuestionOut]:
    base = question_service.get_question(question_id=question_id)
    data = {
        "question_text": body.question_text if body.question_text is not None else base.question_text,
        "option_a": body.option_a if body.option_a is not None else base.option_a,
        "option_b": body.option_b if body.option_b is not None else base.option_b,
        "option_c": body.option_c if body.option_c is not None else base.option_c,
        "option_d": body.option_d if body.option_d is not None else base.option_d,
        "correct_option": body.correct_option if body.correct_option is not None else base.correct_option,
    }
    updated = question_service.patch_question(
        question_id=question_id,
        actor_id=examiner.user_id,
        payload=QuestionPayload(**data),
    )
    return success_envelope(_to_out(updated), request_id=get_request_id())


@router.delete(
    "/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    response_class=Response,
)
def delete_question(
    question_id: uuid.UUID,
    _examiner: ExaminerUserDep,
    _csrf: CsrfProtectedDep,
    question_service: Annotated[QuestionService, Depends(get_question_service)],
) -> None:
    question_service.delete_question(question_id=question_id)
