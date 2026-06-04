# MCQ Online Test Platform

Monorepo scaffold for the role-based MCQ examination system (Examinee + Examiner portals).

**Documentation:** [docs/MCQ_Test_Platform_PRD.md](docs/MCQ_Test_Platform_PRD.md) · [docs/MCQ_Platform_ERD.md](docs/MCQ_Platform_ERD.md) · [docs/MCQ_Platform_Development_Plan.md](docs/MCQ_Platform_Development_Plan.md)

**UX reference (read-only):** [SampleUI/](SampleUI/) — implement production UI in [frontend/](frontend/).

## Prerequisites

- Node.js 20+
- [pnpm](https://pnpm.io/)
- Python 3.12+
- Docker Desktop (or Docker Engine + Compose)

## Quick start

### 1. Environment

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env.local
```

### 2. Backend stack (Postgres, Redis, API)

```bash
make dev-up
```

Verify:

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/ready
curl http://localhost:8000/api/v1/openapi.json
```

Stop:

```bash
make dev-down
```

### 3. Frontend (host)

```bash
cd frontend && pnpm install && pnpm dev
```

Open http://localhost:3000 — placeholder routes:

- `/`
- `/exam/test`
- `/exam/results`
- `/examiner/dashboard`

### 4. Backend tests (local, without Docker)

```bash
make install-backend
make backend-test
```

## Repository layout

| Path | Purpose |
|------|---------|
| `frontend/` | Next.js 16 app (scaffold) |
| `backend/` | FastAPI API (health/ready only) |
| `infra/` | Docker Compose for dev |
| `scripts/` | CLI stubs (bootstrap, seed) |
| `SampleUI/` | Reference UI — do not modify for production |

## Common commands

| Command | Description |
|---------|-------------|
| `make dev-up` | Start Postgres, Redis, API |
| `make dev-down` | Stop Compose stack |
| `make backend-test` | Run pytest smoke tests |
| `make backend-lint` | Ruff check + format |
| `make frontend-dev` | Next.js dev server |
| `make frontend-build` | Production build |

## Phase status

**Phase 0 (scaffold):** Infrastructure endpoints only — no auth, migrations, or business APIs yet.

## Verification (Phase 0)

| Check | Command |
|-------|---------|
| API health | `curl http://localhost:8000/api/v1/health` |
| API readiness | `curl http://localhost:8000/api/v1/ready` (requires Postgres + Redis) |
| OpenAPI | `curl http://localhost:8000/api/v1/openapi.json` |
| Backend tests | `make backend-test` |
| Frontend build | `cd frontend && pnpm install && pnpm build` |
| Compose stack | `make dev-up` |

After first `pnpm install` in `frontend/`, commit `pnpm-lock.yaml` for CI caching.
