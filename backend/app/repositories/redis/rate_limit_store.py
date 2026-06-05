"""IP-based rate limiting in Redis."""

from __future__ import annotations

from redis import Redis

from app.core.config import settings


class RateLimitStore:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    def check_and_increment(
        self,
        key: str,
        *,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, int]:
        """Return (allowed, retry_after_seconds)."""
        count = self._redis.incr(key)
        if count == 1:
            self._redis.expire(key, window_seconds)
        if count > max_requests:
            ttl = self._redis.ttl(key)
            return False, max(ttl, 1)
        return True, 0
