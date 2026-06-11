"""Examinee test flow endpoints (PRD §9.6.4)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Response, status

from app.api.openapi import SECURITY_SESSION, SECURITY_SESSION_CSRF, problem_responses
from app.core.auth import CsrfProtectedDep, ExamineeUserDep
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


@router.get(
    "/sessions/current",
    response_model=SuccessResponse[ExamineeSessionResource],
    summary="Get current test session",
    response_description="Summary of the examinee's active test session.",
    responses=problem_responses(
        401,
        403,
        404,
        overrides={404: {"description": "No active test session was found for this examinee."}},
    ),
    openapi_extra=SECURITY_SESSION,
)
def get_current_session(
    examinee: ExamineeUserDep,
    test_session_service: Annotated[TestSessionService, Depends(get_test_session_service)],
) -> SuccessResponse[ExamineeSessionResource]:
    """Return the examinee's active (in-progress) test session.

    Includes progress (`answered_count`, `current_position`) and the session
    expiry time. Use this to resume a test after a page reload.
    """
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
    summary="Get question at position",
    response_description="The question at the requested position, with any previously selected option.",
    responses=problem_responses(400, 401, 403, 404),
    openapi_extra=SECURITY_SESSION,
)
def get_question_at_position(
    session_id: uuid.UUID,
    position: int,
    examinee: ExamineeUserDep,
    test_session_service: Annotated[TestSessionService, Depends(get_test_session_service)],
) -> SuccessResponse[ExamineeQuestionAtPositionResource]:
    """Fetch the question at a given position (1-50) in the examinee's session.

    The correct answer is never included. The response also returns the
    examinee's previously selected option for that question, if any.
    """
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
    summary="Save or update an answer",
    response_description="The saved response and the updated answered count.",
    responses=problem_responses(
        400,
        401,
        403,
        404,
        409,
        overrides={
            409: {
                "description": "Concurrency conflict — the response was modified after the "
                "timestamp given in If-Unmodified-Since."
            }
        },
    ),
    openapi_extra=SECURITY_SESSION_CSRF,
)
def save_response(
    session_id: uuid.UUID,
    question_id: uuid.UUID,
    body: SaveResponseRequest,
    examinee: ExamineeUserDep,
    _csrf: CsrfProtectedDep,
    test_session_service: Annotated[TestSessionService, Depends(get_test_session_service)],
    if_unmodified_since: Annotated[
        str | None,
        Header(
            alias="If-Unmodified-Since",
            description=(
                "Optional optimistic-concurrency guard (RFC 9110 HTTP-date). If the "
                "stored response was updated after this timestamp, the save is "
                "rejected with 409."
            ),
        ),
    ] = None,
) -> SuccessResponse[SaveResponseResult]:
    """Save, change, or clear the selected option for a question.

    Send `selected_option: null` to clear an answer. Requires the
    `X-CSRF-Token` header. Supports optimistic concurrency via the
    `If-Unmodified-Since` header.
    """
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
    summary="Submit the test for scoring",
    response_description="Final score breakdown for the submitted session.",
    responses=problem_responses(
        400,
        401,
        403,
        404,
        409,
        overrides={409: {"description": "The session has already been submitted."}},
    ),
    openapi_extra=SECURITY_SESSION_CSRF,
)
def submit_session(
    session_id: uuid.UUID,
    body: SubmitSessionRequest,
    examinee: ExamineeUserDep,
    _csrf: CsrfProtectedDep,
    scoring_service: Annotated[ScoringService, Depends(get_scoring_service)],
    idempotency_key: Annotated[
        str | None,
        Header(
            alias="Idempotency-Key",
            description=(
                "Optional client-generated key making the submission retry-safe: "
                "repeated submits with the same key return the original result "
                "instead of failing."
            ),
        ),
    ] = None,
) -> SuccessResponse[SubmitSessionResult]:
    """Submit the test session for scoring. This action is irreversible.

    The request body must include `confirm: true`. Requires the
    `X-CSRF-Token` header. Pass an `Idempotency-Key` header to make retries
    safe — duplicate submissions with the same key return the original score.
    """
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


@router.get(
    "/sessions/{session_id}/review",
    response_model=SuccessResponse[ReviewResult],
    summary="Review submitted answers",
    response_description="Per-question review including correct answers.",
    responses=problem_responses(
        401,
        403,
        404,
        overrides={
            404: {"description": "Session not found, or it has not been submitted yet."}
        },
    ),
    openapi_extra=SECURITY_SESSION,
)
def get_review(
    session_id: uuid.UUID,
    examinee: ExamineeUserDep,
    test_session_service: Annotated[TestSessionService, Depends(get_test_session_service)],
) -> SuccessResponse[ReviewResult]:
    """Return the post-submission review for a completed session.

    Only available after the session has been submitted. Each item includes
    the examinee's selected option, the correct option, and correctness.
    """
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


@router.get(
    "/me/data-export",
    summary="Export personal data (GDPR)",
    responses={
        200: {
            "description": "JSON file download containing all personal data held for the examinee.",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "description": "Complete personal-data export (profile, sessions, responses).",
                    }
                }
            },
            "headers": {
                "Content-Disposition": {
                    "description": 'Attachment with a generated filename, e.g. attachment; filename="data-export.json".',
                    "schema": {"type": "string"},
                }
            },
        },
        **problem_responses(401, 403),
    },
    openapi_extra=SECURITY_SESSION,
)
def data_export(
    examinee: ExamineeUserDep,
    gdpr_service: Annotated[GdprService, Depends(get_gdpr_service)],
) -> Response:
    """Download all personal data held for the authenticated examinee.

    Returns a JSON file as an attachment (GDPR Art. 20 data portability).
    This endpoint bypasses the standard `SuccessResponse` envelope.
    """
    export = gdpr_service.export_examinee_data(user_id=examinee.user_id)
    return Response(
        content=export.json_payload,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{export.filename}"'},
    )
