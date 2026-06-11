"""Shared API response envelopes."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseMeta(BaseModel):
    """Per-request metadata included in every success envelope."""

    request_id: str = Field(
        description="Unique request identifier; matches the X-Request-Id response header.",
        examples=["9f1b2c3d4e5f6a7b"],
    )


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success envelope wrapping every JSON response payload."""

    data: T = Field(description="The endpoint-specific response payload.")
    meta: ResponseMeta = Field(description="Request metadata for log correlation.")


def success_envelope(data: T, *, request_id: str) -> SuccessResponse[T]:
    return SuccessResponse(data=data, meta=ResponseMeta(request_id=request_id))
