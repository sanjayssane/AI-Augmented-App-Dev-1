"""Examiner session results endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.api.openapi import SECURITY_SESSION, problem_responses
from app.core.auth import ExaminerUserDep
from app.core.deps import get_results_service
from app.core.request_id import get_request_id
from app.schemas.common import SuccessResponse, success_envelope
from app.schemas.examiner import (
    SessionDetailOut,
    SessionListData,
    SessionQuestionResultOut,
    SessionSummaryOut,
)
from app.services.results_service import ResultsService

router = APIRouter(prefix="/examiner/sessions")


@router.get(
    "",
    response_model=SuccessResponse[SessionListData],
    summary="List test sessions",
    response_description="A page of test session summaries.",
    responses=problem_responses(400, 401, 403),
    openapi_extra=SECURITY_SESSION,
)
def list_sessions(
    _examiner: ExaminerUserDep,
    results_service: Annotated[ResultsService, Depends(get_results_service)],
    limit: int = Query(default=50, ge=1, le=100, description="Page size (1-100)."),
    cursor: uuid.UUID | None = Query(
        default=None,
        description="Cursor for pagination — pass the `next_cursor` from the previous page.",
    ),
) -> SuccessResponse[SessionListData]:
    """List examinee test sessions (all statuses) with cursor-based pagination.

    Each summary includes the examinee's PRN and name, the session status,
    score, and submission time.
    """
    rows, next_cursor = results_service.list_sessions(limit=limit, cursor=cursor)
    return success_envelope(
        SessionListData(
            items=[
                SessionSummaryOut(
                    session_id=row.session_id,
                    status=row.status,
                    score=row.score,
                    submitted_at=row.submitted_at,
                    prn=row.prn,
                    name=row.name,
                )
                for row in rows
            ],
            next_cursor=next_cursor,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/export",
    summary="Export sessions as CSV",
    responses={
        200: {
            "description": "CSV file download of all test sessions.",
            "content": {
                "text/csv": {
                    "schema": {"type": "string"},
                    "example": "session_id,prn,name,status,score,submitted_at\n...",
                }
            },
            "headers": {
                "Content-Disposition": {
                    "description": 'attachment; filename="sessions-export.csv"',
                    "schema": {"type": "string"},
                }
            },
        },
        **problem_responses(401, 403),
    },
    openapi_extra=SECURITY_SESSION,
)
def export_sessions(
    _examiner: ExaminerUserDep,
    results_service: Annotated[ResultsService, Depends(get_results_service)],
    anonymised: bool = Query(
        default=False,
        description="When true, personal identifiers (PRN, name) are omitted from the export.",
    ),
) -> Response:
    """Download all test sessions as a CSV attachment.

    Set `anonymised=true` to exclude personal identifiers. This endpoint
    bypasses the standard `SuccessResponse` envelope.
    """
    csv_data = results_service.export_sessions_csv(anonymised=anonymised)
    return Response(
        content=csv_data.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="sessions-export.csv"'},
    )


@router.get(
    "/{session_id}",
    response_model=SuccessResponse[SessionDetailOut],
    summary="Get session detail",
    response_description="Full session detail including per-question results.",
    responses=problem_responses(401, 403, 404),
    openapi_extra=SECURITY_SESSION,
)
def session_detail(
    session_id: uuid.UUID,
    _examiner: ExaminerUserDep,
    results_service: Annotated[ResultsService, Depends(get_results_service)],
) -> SuccessResponse[SessionDetailOut]:
    """Return a single test session with its per-question responses.

    Includes the examinee's identity, selection mode, score, and for each
    question the selected option, correct option, and correctness.
    """
    detail = results_service.get_session_detail(session_id=session_id)
    return success_envelope(
        SessionDetailOut(
            session_id=detail.session_id,
            user_id=detail.user_id,
            status=detail.status,
            score=detail.score,
            started_at=detail.started_at,
            submitted_at=detail.submitted_at,
            selection_mode=detail.selection_mode,
            prn=detail.prn,
            name=detail.name,
            responses=[
                SessionQuestionResultOut(
                    question_id=r.question_id,
                    position=r.position,
                    question_text=r.question_text,
                    selected_option=r.selected_option,
                    correct_option=r.correct_option,
                    is_correct=r.is_correct,
                )
                for r in detail.responses
            ],
        ),
        request_id=get_request_id(),
    )
