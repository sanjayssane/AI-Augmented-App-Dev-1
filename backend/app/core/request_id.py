"""Request ID utilities."""

from __future__ import annotations

import uuid
from contextvars import ContextVar

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    rid = request_id_ctx.get()
    if rid:
        return rid
    return str(uuid.uuid4())


def set_request_id(request_id: str) -> None:
    request_id_ctx.set(request_id)
