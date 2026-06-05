"""CSRF token storage in Redis."""

from __future__ import annotations

import secrets

from redis import Redis

from app.core.config import settings


class CsrfStore:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    def _key(self, token: str) -> str:
        return f"csrf:{token}"

    def issue_token(self) -> str:
        token = secrets.token_urlsafe(32)
        self._redis.setex(self._key(token), settings.csrf_token_ttl_seconds, "1")
        return token

    def validate(self, token: str) -> bool:
        return bool(self._redis.exists(self._key(token)))
