"""Examinee test flow endpoints (PRD §9.6.4)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Response, status

from app.core.auth import ExamineeUserDep
from app.core.deps import get_gdpr_service, get_scoring_service, get_test_session_service
from app.core.request_id import get_request_id
from app.domain.concurrency import parse_if_unmodified_since
from app.schemas.common import SuccessResponse, success_envelope
from app.schemas.examinee import (
    ExamineeQuestionAtPositionResource,
    ExamineeSessionResource,
    QuestionOption,
    ReviewItem,
    ReviewResult,
    SaveResponseRequest,
    SaveResponseResult,
    SessionQuestionPayload,
    SubmitSessionRequest,
    SubmitSessionResult,
)
from app.services.gdpr_service import GdprService
from app.services.scoring_service import ScoringService
from app.services.test_session_service import TestSessionService

router = APIRouter(prefix="/examinee")


@router.get("/sessions/current", response_model=SuccessResponse[ExamineeSessionResource])
def get_current_session(
    examinee: ExamineeUserDep,
    test_session_service: Annotated[TestSessionService, Depends(get_test_session_service)],
) -> SuccessResponse[ExamineeSessionResource]:
    view = test_session_service.get_current_session(user_id=examinee.user_id)
    return success_envelope(
        ExamineeSessionResource(
            session_id=view.session_id,
            status=view.status,
            answered_count=view.answered_count,
            current_position=view.current_position,
            started_at=view.started_at,
            expires_at=view.expires_at,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/sessions/{session_id}/questions/{position}",
    response_model=SuccessResponse[ExamineeQuestionAtPositionResource],
)
def get_question_at_position(
    session_id: uuid.UUID,
    position: int,
    examinee: ExamineeUserDep,
    test_session_service: Annotated[TestSessionService, Depends(get_test_session_service)],
) -> SuccessResponse[ExamineeQuestionAtPositionResource]:
    view = test_session_service.get_question_at_position(
        user_id=examinee.user_id,
        session_id=session_id,
        position=position,
    )
    return success_envelope(
        ExamineeQuestionAtPositionResource(
            position=view.position,
            total=view.total,
            question=SessionQuestionPayload(
                question_id=view.question_id,
                question_text=view.question_text,
                options=[
                    QuestionOption(key="A", text=view.option_a),
                    QuestionOption(key="B", text=view.option_b),
                    QuestionOption(key="C", text=view.option_c),
                    QuestionOption(key="D", text=view.option_d),
                ],
            ),
            selected_option=view.selected_option,
            answered_count=view.answered_count,
        ),
        request_id=get_request_id(),
    )


@router.put(
    "/sessions/{session_id}/responses/{question_id}",
    response_model=SuccessResponse[SaveResponseResult],
)
def save_response(
    session_id: uuid.UUID,
    question_id: uuid.UUID,
    body: SaveResponseRequest,
    examinee: ExamineeUserDep,
    test_session_service: Annotated[TestSessionService, Depends(get_test_session_service)],
    if_unmodified_since: Annotated[str | None, Header(alias="If-Unmodified-Since")] = None,
) -> SuccessResponse[SaveResponseResult]:
    parsed_if_unmodified_since = parse_if_unmodified_since(if_unmodified_since)
    view = test_session_service.save_response(
        user_id=examinee.user_id,
        session_id=session_id,
        question_id=question_id,
        selected_option=body.selected_option,
        if_unmodified_since=parsed_if_unmodified_since,
    )
    return success_envelope(
        SaveResponseResult(
            question_id=view.question_id,
            selected_option=view.selected_option,
            updated_at=view.updated_at,
            answered_count=view.answered_count,
        ),
        request_id=get_request_id(),
    )


@router.post(
    "/sessions/{session_id}/submit",
    response_model=SuccessResponse[SubmitSessionResult],
    status_code=status.HTTP_201_CREATED,
)
def submit_session(
    session_id: uuid.UUID,
    body: SubmitSessionRequest,
    examinee: ExamineeUserDep,
    scoring_service: Annotated[ScoringService, Depends(get_scoring_service)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> SuccessResponse[SubmitSessionResult]:
    _ = body.confirm
    view = scoring_service.submit_session(
        user_id=examinee.user_id,
        session_id=session_id,
        idempotency_key=idempotency_key,
    )
    return success_envelope(
        SubmitSessionResult(
            session_id=view.session_id,
            status=view.status,
            score=view.score,
            max_score=view.max_score,
            correct_count=view.correct_count,
            incorrect_count=view.incorrect_count,
            unattempted_count=view.unattempted_count,
            submitted_at=view.submitted_at,
        ),
        request_id=get_request_id(),
    )


@router.get("/sessions/{session_id}/review", response_model=SuccessResponse[ReviewResult])
def get_review(
    session_id: uuid.UUID,
    examinee: ExamineeUserDep,
    test_session_service: Annotated[TestSessionService, Depends(get_test_session_service)],
) -> SuccessResponse[ReviewResult]:
    items = test_session_service.get_review(
        user_id=examinee.user_id,
        session_id=session_id,
    )
    return success_envelope(
        ReviewResult(
            items=[
                ReviewItem(
                    position=item.position,
                    question_text=item.question_text,
                    options=[
                        QuestionOption(key="A", text=item.option_a),
                        QuestionOption(key="B", text=item.option_b),
                        QuestionOption(key="C", text=item.option_c),
                        QuestionOption(key="D", text=item.option_d),
                    ],
                    selected_option=item.selected_option,
                    correct_option=item.correct_option,
                    is_correct=item.is_correct,
                )
                for item in items
            ]
        ),
        request_id=get_request_id(),
    )


@router.get("/me/data-export")
def data_export(
    examinee: ExamineeUserDep,
    gdpr_service: Annotated[GdprService, Depends(get_gdpr_service)],
) -> Response:
    export = gdpr_service.export_examinee_data(user_id=examinee.user_id)
    return Response(
        content=export.json_payload,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{export.filename}"'},
    )
