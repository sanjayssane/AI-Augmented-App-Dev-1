"""Submit idempotency records in Redis."""

from __future__ import annotations

import json

from redis import Redis

from app.core.config import settings


class SubmitIdempotencyStore:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    def _key(self, idempotency_key: str) -> str:
        return f"idempotency:submit:{idempotency_key}"

    def get(self, idempotency_key: str) -> dict | None:
        raw = self._redis.get(self._key(idempotency_key))
        if not raw:
            return None
        return json.loads(raw)

    def put(self, idempotency_key: str, payload: dict) -> None:
        self._redis.setex(
            self._key(idempotency_key),
            settings.submit_idempotency_ttl_seconds,
            json.dumps(payload),
        )
