# MCQ Platform Backend

FastAPI application (Phase 0 scaffold).

## Local run

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Requires `DATABASE_URL` and `REDIS_URL` for `/api/v1/ready`.

## Docker

Started via `make dev-up` from repository root.
