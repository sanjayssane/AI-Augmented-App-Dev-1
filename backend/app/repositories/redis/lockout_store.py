"""Examiner login lockout counter in Redis."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from redis import Redis

from app.core.config import settings


@dataclass
class LockoutState:
    failed_count: int
    window_start: datetime
    locked_until: datetime | None


class LockoutStore:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    def _key(self, username: str) -> str:
        return f"lockout:{username.strip().lower()}"

    def _load(self, username: str) -> LockoutState | None:
        raw = self._redis.get(self._key(username))
        if not raw:
            return None
        data = json.loads(raw)
        return LockoutState(
            failed_count=data["failed_count"],
            window_start=datetime.fromisoformat(data["window_start"]),
            locked_until=(
                datetime.fromisoformat(data["locked_until"]) if data.get("locked_until") else None
            ),
        )

    def _save(self, username: str, state: LockoutState) -> None:
        ttl = max(settings.lockout_window_seconds, settings.lockout_cooldown_seconds)
        payload = {
            "failed_count": state.failed_count,
            "window_start": state.window_start.isoformat(),
            "locked_until": state.locked_until.isoformat() if state.locked_until else None,
        }
        self._redis.setex(self._key(username), ttl, json.dumps(payload))

    def is_locked(self, username: str) -> datetime | None:
        state = self._load(username)
        if not state or not state.locked_until:
            return None
        now = datetime.now(UTC)
        if state.locked_until > now:
            return state.locked_until
        return None

    def record_failure(self, username: str) -> LockoutState:
        now = datetime.now(UTC)
        state = self._load(username)
        window = timedelta(seconds=settings.lockout_window_seconds)

        if state is None or (now - state.window_start) > window:
            state = LockoutState(failed_count=0, window_start=now, locked_until=None)

        state.failed_count += 1
        if state.failed_count >= settings.lockout_max_attempts:
            state.locked_until = now + timedelta(seconds=settings.lockout_cooldown_seconds)

        self._save(username, state)
        return state

    def clear(self, username: str) -> None:
        self._redis.delete(self._key(username))
