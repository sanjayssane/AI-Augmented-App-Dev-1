"""Optimistic concurrency helpers (PRD §9.6.1)."""

from __future__ import annotations

from datetime import UTC, datetime


def parse_if_unmodified_since(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed
    except ValueError:
        return None


def is_stale(client_ts: datetime | None, server_ts: datetime) -> bool:
    if client_ts is None:
        return False
    server = server_ts if server_ts.tzinfo else server_ts.replace(tzinfo=UTC)
    client = client_ts if client_ts.tzinfo else client_ts.replace(tzinfo=UTC)
    return client < server
