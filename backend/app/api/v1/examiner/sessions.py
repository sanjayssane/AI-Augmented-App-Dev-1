"""Examiner session results endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

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


@router.get("", response_model=SuccessResponse[SessionListData])
def list_sessions(
    _examiner: ExaminerUserDep,
    results_service: Annotated[ResultsService, Depends(get_results_service)],
    limit: int = Query(default=50, ge=1, le=100),
    cursor: uuid.UUID | None = Query(default=None),
) -> SuccessResponse[SessionListData]:
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


@router.get("/export")
def export_sessions(
    _examiner: ExaminerUserDep,
    results_service: Annotated[ResultsService, Depends(get_results_service)],
    anonymised: bool = Query(default=False),
) -> Response:
    csv_data = results_service.export_sessions_csv(anonymised=anonymised)
    return Response(
        content=csv_data.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="sessions-export.csv"'},
    )


@router.get("/{session_id}", response_model=SuccessResponse[SessionDetailOut])
def session_detail(
    session_id: uuid.UUID,
    _examiner: ExaminerUserDep,
    results_service: Annotated[ResultsService, Depends(get_results_service)],
) -> SuccessResponse[SessionDetailOut]:
    detail = results_service.get_session_detail(session_id=session_id)
    return success_envelope(
        SessionDetailOut(
            session_id=detail.session_id,
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
