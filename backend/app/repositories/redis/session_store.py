"""Server-side session storage in Redis."""

from __future__ import annotations

import json
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from redis import Redis

from app.core.config import settings
from app.models.enums import UserRole


@dataclass
class ServerSession:
    session_token: str
    user_id: uuid.UUID
    role: UserRole
    created_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    csrf_token: str


class SessionStore:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    def _session_key(self, token: str) -> str:
        return f"session:{token}"

    def _user_sessions_key(self, user_id: uuid.UUID) -> str:
        return f"user_sessions:{user_id}"

    def _ttl_for_role(self, role: UserRole) -> int:
        if role == UserRole.EXAMINER:
            return settings.examiner_session_ttl_seconds
        return settings.examinee_session_ttl_seconds

    def create_session(self, user_id: uuid.UUID, role: UserRole) -> str:
        token = secrets.token_urlsafe(32)
        now = datetime.now(UTC)
        ttl = self._ttl_for_role(role)
        expires_at = now + timedelta(seconds=ttl)
        csrf_token = secrets.token_urlsafe(32)
        payload = {
            "user_id": str(user_id),
            "role": role.value,
            "created_at": now.isoformat(),
            "last_seen_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "csrf_token": csrf_token,
        }
        session_key = self._session_key(token)
        user_key = self._user_sessions_key(user_id)
        pipe = self._redis.pipeline()
        pipe.setex(session_key, ttl, json.dumps(payload))
        pipe.sadd(user_key, token)
        pipe.expire(user_key, ttl)
        pipe.execute()
        return token

    def invalidate_all_for_user(self, user_id: uuid.UUID) -> None:
        user_key = self._user_sessions_key(user_id)
        tokens = self._redis.smembers(user_key)
        if not tokens:
            return
        pipe = self._redis.pipeline()
        for token in tokens:
            pipe.delete(self._session_key(token))
        pipe.delete(user_key)
        pipe.execute()

    def delete_session(self, token: str, user_id: uuid.UUID | None = None) -> None:
        self._redis.delete(self._session_key(token))
        if user_id is not None:
            self._redis.srem(self._user_sessions_key(user_id), token)

    def touch_session(self, token: str) -> None:
        raw = self._redis.get(self._session_key(token))
        if not raw:
            return
        data = json.loads(raw)
        role = UserRole(data["role"])
        ttl = self._ttl_for_role(role)
        now = datetime.now(UTC)
        data["last_seen_at"] = now.isoformat()
        data["expires_at"] = (now + timedelta(seconds=ttl)).isoformat()
        self._redis.setex(self._session_key(token), ttl, json.dumps(data))

    def get_session(self, token: str) -> ServerSession | None:
        raw = self._redis.get(self._session_key(token))
        if not raw:
            return None
        data = json.loads(raw)
        return ServerSession(
            session_token=token,
            user_id=uuid.UUID(data["user_id"]),
            role=UserRole(data["role"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_seen_at=datetime.fromisoformat(data["last_seen_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            csrf_token=data["csrf_token"],
        )
