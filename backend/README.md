# MCQ Platform Backend

FastAPI application with PostgreSQL (app + audit schemas) and Redis.

## Prerequisites

- Python 3.12+
- PostgreSQL 15+ (via `make dev-up` or local install)
- Redis 7+ (for session/auth features in later phases)

## Local setup

```bash
# From repository root
make dev-up          # Postgres + Redis + API (Docker)
make install-backend
make db-migrate      # Apply Alembic migrations 001–003
```

Set `DATABASE_URL` if not using defaults (see `.env.example` at repo root):

```text
postgresql+psycopg://mcq:mcq_dev_password@localhost:5432/mcq_platform
```

## Database migrations

Migrations live in `alembic/versions/`:

| Revision | Description |
|---|---|
| `001_initial_app` | App tables, enums, partial unique indexes |
| `002_audit_schema` | `audit.audit_logs` append-only table |
| `003_seed_platform_settings` | Default `PlatformSettings` keys |

```bash
cd backend
alembic upgrade head      # Apply all
alembic downgrade -1      # Roll back one (dev only)
alembic current           # Show revision
```

From repo root: `make db-migrate`, `make db-downgrade`, `make db-revision MSG='your message'`.

## Seed data (dev)

After migrations:

```bash
python scripts/bootstrap_examiner.py --username admin --password 'ChangeMe123456!'
python scripts/seed_questions.py --count 55
```

## Run API

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

`/api/v1/health` is public; `/api/v1/ready` checks Postgres and Redis when configured.

## Redis keys

See [docs/redis-keys.md](docs/redis-keys.md) for session, lockout, rate limit, and idempotency key patterns (no SQL migrations).

## Audit schema

`audit.audit_logs` is append-only. Restrict UPDATE/DELETE on the application DB role in production (manual GRANT or infra script).
