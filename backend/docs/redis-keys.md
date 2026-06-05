# Redis key design

Non-relational stores required by `docs/MCQ_Platform_ERD.md` §5. These are **not** managed by Alembic.

## Key patterns

| Key pattern | Purpose | Value shape | TTL |
|---|---|---|---|
| `session:{token}` | Server-side auth session (HttpOnly cookie → token) | JSON: `user_id`, `role`, `created_at`, `last_seen_at`, `expires_at`, `csrf_token` | Examiner: 60 min inactivity; Examinee: 4 h inactivity (PRD §3.1.4) |
| `lockout:{username}` | Examiner login failure counter | JSON: `failed_count`, `window_start`, `locked_until` | 15 min lockout window after 5 failures |
| `ratelimit:register:{ip}` | Examinee registration / entry rate limit | Integer counter | 1 hour (10 requests / IP / hour per PRD §4.4) |
| `idempotency:submit:{key}` | Idempotent End Test (`Idempotency-Key` header) | JSON: `session_id`, `response_body` | 24 hours |

## Conventions

- Use a single Redis DB index (default `0`) unless environments require isolation.
- Prefix all keys as above to avoid collisions.
- Set TTL on every write; refresh session TTL on authenticated activity.
- Never store PRN, name, or password in Redis values.

## Implementation

Repository modules under `app/repositories/redis/` (Phase 1.3+) should encapsulate get/set/delete for each pattern.

Submit idempotency uses **Redis only** for MVP (not PostgreSQL).
