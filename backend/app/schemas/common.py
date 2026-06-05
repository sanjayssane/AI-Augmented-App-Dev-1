"""Shared API response envelopes."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseMeta(BaseModel):
    request_id: str


class SuccessResponse(BaseModel, Generic[T]):
    data: T
    meta: ResponseMeta


def success_envelope(data: T, *, request_id: str) -> SuccessResponse[T]:
    return SuccessResponse(data=data, meta=ResponseMeta(request_id=request_id))
