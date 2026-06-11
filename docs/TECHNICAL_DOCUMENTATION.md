# MCQ Online Test Platform — Technical Documentation

> Audience: developers and operators working on this codebase.
> Related docs: [PRD](MCQ_Test_Platform_PRD.md) · [ERD](MCQ_Platform_ERD.md) · [Development Plan](MCQ_Platform_Development_Plan.md) · [Deployment Guide](DEPLOYMENT.md) · [Redis Keys](../backend/docs/redis-keys.md)

---

## 1. System Overview

A role-based MCQ examination platform with two portals:

- **Examinee portal** — enter with PRN + name, take a 50-question MCQ test, submit, review results, export personal data (GDPR).
- **Examiner portal** — manage the question bank, view/export test session results, manage platform settings, create examiner accounts, and process GDPR erasure requests (admin only).

### High-level architecture

```mermaid
flowchart LR
  Browser --> FE["Next.js 16 (App Router)\n:3000"]
  FE -->|"fetch, credentials: include\n+ X-CSRF-Token"| API["FastAPI\n:8000 (/api/v1)"]
  API --> PG[("PostgreSQL 15\nusers, questions, sessions,\nresponses, audit, settings")]
  API --> RD[("Redis 7\nsessions, CSRF, lockout,\nrate limits, idempotency")]
  JOBS["Background jobs (CLI)\nexpiry / purge / erasure"] --> PG
```

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16.2 (App Router), React 19, TypeScript 5.7, Tailwind CSS 4, shadcn/ui (Radix) |
| Backend | Python 3.12, FastAPI ≥0.115, SQLAlchemy 2.0, Pydantic v2, Uvicorn |
| Database | PostgreSQL 15 (psycopg 3), Alembic migrations |
| Cache / session store | Redis 7 |
| Auth | Opaque server-side sessions (Redis) + HttpOnly cookie + CSRF tokens — **no JWT** |
| Testing | pytest (backend), Playwright + axe-core (frontend E2E) |
| Infra | Docker Compose (dev), GitHub Actions CI, nginx (planned) |

---

## 2. Repository Layout

| Path | Purpose |
|------|---------|
| `backend/` | FastAPI application, Alembic migrations, pytest suite |
| `frontend/` | Next.js application |
| `infra/` | Docker Compose for the dev stack (postgres, redis, api) |
| `scripts/` | Operational CLIs: `bootstrap_examiner.py`, `seed_questions.py` |
| `postman/` | Postman collection, environment, exported OpenAPI spec |
| `docs/` | Product and technical documentation |
| `SampleUI/` | Read-only UX reference — not production code |
| `.github/workflows/` | CI pipelines (`ci.yml`, `dependency-review.yml`) |

---

## 3. Backend

### 3.1 Application structure (`backend/app/`)

The backend follows a layered architecture: **API → Services → Repositories → Database**, with pure business rules isolated in `domain/`.

| Module | Responsibility |
|--------|----------------|
| `main.py` | App factory: CORS, middleware, exception handlers, router mounted at `/api/v1` |
| `api/v1/` | Route handlers: `auth.py`, `health.py`, `examinee.py`, `examiner/` (`questions`, `sessions`, `settings`, `users`) |
| `api/middleware.py` | `RequestIdMiddleware` (adds `X-Request-Id`), `SecurityHeadersMiddleware` |
| `api/exception_handlers.py` | RFC 7807 `application/problem+json` error responses |
| `core/` | Config (`config.py`), DB engine (`database.py`), Redis factory (`redis.py`), DI wiring (`deps.py`), auth guards (`auth.py`), cookies, encryption, passwords, request-ID context |
| `models/` | SQLAlchemy ORM models + PostgreSQL enums |
| `schemas/` | Pydantic request/response DTOs (`auth`, `examinee`, `examiner`, `common`, `errors`) |
| `repositories/` | PostgreSQL data access (one repository per aggregate) + `uow.py` unit-of-work |
| `repositories/redis/` | Redis stores: sessions, lockout, rate limit, CSRF, submit idempotency |
| `services/` | Business logic: `auth_service`, `test_session_service`, `scoring_service`, `question_service`, `results_service`, `settings_service`, `user_admin_service`, `gdpr_service`, `audit_service`, `retention_job_service`, `csrf_service` |
| `domain/` | Pure rules (no I/O): `scoring`, `session_rules`, `question_selection`, `concurrency`, `validation`, `versioning`, `gdpr` |
| `jobs/` | CLI-runnable jobs: `session_expiry_job`, `retention_purge_job`, `erasure_processor_job` |

### 3.2 Configuration

Settings load from environment / `.env` via Pydantic Settings (`app/core/config.py`). Key defaults:

| Setting | Default |
|---------|---------|
| `DATABASE_URL` | `postgresql+psycopg://mcq:mcq_dev_password@localhost:5432/mcq_platform` |
| `REDIS_URL` | `redis://localhost:6379/0` |
| `CORS_ORIGINS` | `http://localhost:3000` |
| Examiner session TTL | 3600 s (1 h) |
| Examinee session TTL | 14400 s (4 h) |
| Login lockout | 5 failures / 900 s window, 900 s cooldown |
| Examinee entry rate limit | 10 requests / hour / IP |
| Submit idempotency TTL | 86400 s (24 h) |
| Minimum active questions | 50 |
| bcrypt rounds | 12 |

---

## 4. API Reference

- **Base URL:** `/api/v1`
- **Interactive docs:** `/api/v1/docs` (Swagger UI), `/api/v1/redoc`, `/api/v1/openapi.json`
- **Success envelope:** `{ "data": ..., "meta": { "request_id": "..." } }`
- **Errors:** RFC 7807 `application/problem+json` with `type`, `title`, `status`, `detail`, `request_id`, optional `errors[]` / `locked_until`
- **Auth legend:** *Session* = valid `session_id` cookie; *CSRF* = `X-CSRF-Token` header; *Admin* = examiner with `is_admin = true`

### Health (public)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness probe |
| GET | `/ready` | Readiness — checks PostgreSQL + Redis (503 if either is down) |

### Auth

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| GET | `/auth/csrf` | Issue pre-login CSRF token | — |
| POST | `/auth/examiner/login` | Examiner login, sets session cookie (1 h) | — |
| POST | `/auth/examinee/entry` | Register or resume examinee, sets cookie (4 h); 201 new / 200 resumed | — |
| POST | `/auth/logout` | Invalidate session, clear cookie | Session + CSRF |
| GET | `/auth/me` | Current user profile + session CSRF token | Session |

### Examinee (examinee role)

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| GET | `/examinee/sessions/current` | Active/latest session summary | Session |
| GET | `/examinee/sessions/{session_id}/questions/{position}` | Question at position 1–50 (correct answer never exposed) | Session |
| PUT | `/examinee/sessions/{session_id}/responses/{question_id}` | Save/clear answer; optional `If-Unmodified-Since` (409 on conflict) | Session + CSRF |
| POST | `/examinee/sessions/{session_id}/submit` | Submit for scoring (201); optional `Idempotency-Key` | Session + CSRF |
| GET | `/examinee/sessions/{session_id}/review` | Post-submission review with correct answers | Session |
| GET | `/examinee/me/data-export` | GDPR JSON data export (file download) | Session |

### Examiner — Questions (examiner role)

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| GET | `/examiner/questions` | Cursor-paginated question list | Session |
| POST | `/examiner/questions` | Create question | Session + CSRF |
| PATCH | `/examiner/questions/{question_id}` | Partial update (increments version, snapshots prior version) | Session + CSRF |
| DELETE | `/examiner/questions/{question_id}` | Soft delete (204); 409 if bank would drop below 50 | Session + CSRF |

### Examiner — Sessions (examiner role)

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| GET | `/examiner/sessions` | Cursor-paginated session summaries | Session |
| GET | `/examiner/sessions/export` | CSV export (`?anonymised=true` optional) | Session |
| GET | `/examiner/sessions/{session_id}` | Full session detail with per-question results | Session |

### Examiner — Users & Settings

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| POST | `/examiner/users/examiners` | Create examiner account (201) | Session + CSRF + Admin |
| POST | `/examiner/users/examinees/{user_id}/erase` | Request GDPR erasure (202) | Session + CSRF + Admin |
| GET | `/examiner/settings` | Read platform settings | Session |
| PATCH | `/examiner/settings` | Update platform settings | Session + CSRF + Admin |

### Notable error responses

| Class | HTTP | Trigger |
|-------|------|---------|
| `InvalidCredentialsError` | 401 | Bad examiner login |
| `AccountLockedError` | 423 | Login lockout (includes `locked_until`) |
| `UnauthenticatedError` / `ForbiddenError` | 401 / 403 | Missing session / wrong role or ownership |
| `CsrfValidationError` | 403 | Missing or invalid `X-CSRF-Token` |
| `ConflictError` / `ExamAlreadyCompletedError` | 409 | Concurrency conflict / retake disabled |
| `RateLimitExceededError` | 429 | Examinee entry rate limit (sends `Retry-After`) |
| `InsufficientQuestionBankError` | 503 | Fewer than 50 active questions |

---

## 5. Authentication & Security

The platform uses **opaque server-side sessions** stored in Redis — no JWTs.

### 5.1 Session flow

```mermaid
sequenceDiagram
  participant B as Browser
  participant A as FastAPI
  participant R as Redis

  B->>A: GET /auth/csrf
  A->>R: SET csrf:{token} (TTL 1h)
  A-->>B: csrf_token
  B->>A: POST /auth/examiner/login (X-CSRF-Token)
  A->>A: bcrypt verify + lockout check
  A->>R: SET session:{token} (TTL 1h/4h)
  A-->>B: Set-Cookie session_id (HttpOnly, SameSite=strict, path=/api/v1)
  B->>A: GET /auth/me (cookie)
  A->>R: GET + touch session (refresh TTL)
  A-->>B: profile + session csrf_token
```

1. **Login/entry** creates a random token (`secrets.token_urlsafe(32)`) stored at `session:{token}` in Redis with role-specific TTL (examiner 1 h, examinee 4 h).
2. The token is delivered as an **HttpOnly cookie** `session_id` (`SameSite=strict`, path `/api/v1`) — never readable by JavaScript.
3. Every authenticated request resolves the cookie against Redis and refreshes the TTL (sliding expiry).
4. **Role guards** (FastAPI dependencies in `core/auth.py`): `CurrentUserDep`, `ExaminerUserDep`, `ExamineeUserDep`, `AdminExaminerDep`.
5. **Logout** deletes the Redis session and clears the cookie.

### 5.2 CSRF protection

- Pre-login token from `GET /auth/csrf` (Redis-backed, 1 h TTL) for login/entry forms.
- Post-login token embedded in the session payload and returned by `GET /auth/me`.
- All mutating authenticated routes require the `X-CSRF-Token` header, compared with `secrets.compare_digest`.

### 5.3 Brute-force & abuse protection

- **Examiner lockout:** 5 failed logins within 15 minutes → HTTP 423 with `locked_until`; cleared on successful login. Successful login also invalidates all prior sessions for that user.
- **Examinee entry rate limit:** 10 requests/hour per IP → HTTP 429 with `Retry-After`.
- **Submit idempotency:** optional `Idempotency-Key` header caches the scoring result for 24 h, preventing duplicate submissions.

### 5.4 PII protection

- Examinee PRN and name are stored **encrypted** (`prn_ciphertext`, `name_ciphertext`) using `cryptography`; lookups use an HMAC `prn_lookup_hash`.
- No PII is stored in Redis values.
- GDPR support: self-service data export (examinee) and admin-triggered erasure jobs processed asynchronously.
- Audit trail: append-only `audit.audit_logs` table (separate schema) recording event type, actor, resource, outcome, IP, and metadata.

---

## 6. Data Model

PostgreSQL via SQLAlchemy 2.0. See [ERD](MCQ_Platform_ERD.md) for the full diagram.

| Table | Purpose | Key fields |
|-------|---------|-----------|
| `users` | Examiners and examinees (single table, role-discriminated) | `user_id` (UUID PK), `role`, `username`/`password_hash`/`is_admin` (examiner), `prn_ciphertext`/`prn_lookup_hash`/`name_ciphertext`/`privacy_acknowledged_at` (examinee), soft delete via `deleted_at` |
| `questions` | Question bank | `question_id`, `question_text`, `option_a`–`option_d`, `correct_option` (A–D), `question_version`, `created_by`, soft delete |
| `question_versions` | Immutable snapshots taken on every edit — used for scoring fidelity | `version_id`, `question_id`, `version_number` (unique per question), full content snapshot, `modified_by` |
| `test_sessions` | One exam attempt | `session_id`, `user_id`, `status` (ACTIVE / COMPLETED / EXPIRED), `selection_mode`, `score`, `start_time`, `end_time`, `expires_at` |
| `session_questions` | The 50 questions pinned to a session | `position` (1–50, unique per session), `question_version_snapshot` |
| `responses` | One row per session question | `selected_option` (nullable), `is_correct` (set at scoring), unique (`session_id`, `question_id`) |
| `platform_settings` | Key-value JSONB settings | Seeded: `retention_days_completed` (730), `allow_examinee_retake` (false), `question_selection_mode` (`FIXED_ORDER`) |
| `audit.audit_logs` | Append-only audit trail (separate `audit` schema) | `event_type`, `actor_id`, `resource_type/id`, `outcome`, `ip_address`, JSONB `metadata` |
| `erasure_jobs` | GDPR erasure queue | `examinee_user_id`, `operator_user_id`, `status` (PENDING / COMPLETED / FAILED) |

### Migrations (Alembic)

| Revision | Description |
|----------|-------------|
| `001_initial_app` | `pgcrypto` extension, enums, all core tables, partial unique indexes |
| `002_audit_schema` | `audit` schema + `audit.audit_logs` |
| `003_seed_platform_settings` | Default platform settings |
| `004_examiner_is_admin` | `users.is_admin` column; first examiner promoted to admin |

Run with `alembic upgrade head` (or `make db-migrate` from the repo root). Redis keys are not migrated — see `backend/docs/redis-keys.md`.

### Redis keys

| Key pattern | Purpose | TTL |
|-------------|---------|-----|
| `session:{token}` | Session JSON (`user_id`, `role`, timestamps, `csrf_token`) | 1 h examiner / 4 h examinee, sliding |
| `user_sessions:{user_id}` | Set of active session tokens per user | Matches session TTL |
| `lockout:{username}` | Login failure counter + lock window | 900 s |
| `auth:examinee_entry:{ip}` | Examinee entry rate-limit counter | 3600 s |
| `idempotency:submit:{key}` | Cached submit result | 24 h |
| `csrf:{token}` | Pre-login CSRF flag | 1 h |

---

## 7. Core Business Flows

### 7.1 Examinee test lifecycle

```mermaid
sequenceDiagram
  participant E as Examinee (browser)
  participant A as FastAPI
  participant P as PostgreSQL

  E->>A: POST /auth/examinee/entry (prn, name, privacy_ack)
  A->>P: Find user by prn_lookup_hash, or create
  A->>P: Create TestSession + 50 SessionQuestions + 50 empty Responses
  A-->>E: 201 (new) / 200 (resume), session cookie
  loop For each question 1..50
    E->>A: GET .../questions/{position}
    E->>A: PUT .../responses/{question_id} (If-Unmodified-Since)
  end
  E->>A: POST .../submit (Idempotency-Key)
  A->>P: Score against version snapshots, mark COMPLETED
  A-->>E: score, correct/incorrect/unattempted
  E->>A: GET .../review (correct answers now visible)
```

- **Session creation** requires ≥ 50 active questions; selection mode is `FIXED_ORDER` (first 50) or `RANDOM_SAMPLE` (shuffled), per platform settings. Each `SessionQuestion` pins a `question_version_snapshot` so later edits don't affect in-flight or completed exams.
- **Resume:** an existing ACTIVE session is returned as-is. **Retake:** only when `allow_examinee_retake` is enabled.
- **Answer saving** uses optimistic concurrency: the client sends `If-Unmodified-Since`; a mismatch returns 409 and the client reloads then retries.
- **Scoring** (`ScoringService.submit_session`): resolves each question's pinned version snapshot, computes correctness, bulk-updates `responses.is_correct`, sets `score` (= correct count, max 50) and `end_time`, marks the session COMPLETED. Idempotency-keyed results are cached in Redis.

### 7.2 Question versioning

Editing a question via `PATCH /examiner/questions/{id}` snapshots the previous content into `question_versions` and increments `questions.question_version`. Scoring always resolves the version a session was created with, guaranteeing reproducible results.

### 7.3 Background jobs (`backend/app/jobs/`)

| Job | Action |
|-----|--------|
| `session_expiry_job` | Marks stale ACTIVE sessions (past `expires_at`) as EXPIRED |
| `retention_purge_job` | Deletes COMPLETED sessions older than `retention_days_completed` |
| `erasure_processor_job` | Processes PENDING GDPR erasure jobs |

Run via `backend/scripts/run_jobs.py` (cron/scheduler in production).

---

## 8. Frontend

### 8.1 Routes (`frontend/app/`)

| Route | Purpose | Guard |
|-------|---------|-------|
| `/` | Landing: role selection, examinee entry form, examiner login; auto-redirects authenticated users | — |
| `/exam/test` | 50-question test UI with navigation, auto-save, submit | `EXAMINEE` + ACTIVE session |
| `/exam/results` | Score summary, per-question review, GDPR data export | `EXAMINEE` |
| `/examiner/dashboard` | Question bank CRUD + results tab (session list, CSV export) | `EXAMINER` |
| `/examiner/sessions/[id]` | Session drill-down with per-question correctness | `EXAMINER` |
| `/examiner/settings` | Platform settings, create examiner, GDPR erasure (admin) | `EXAMINER` |

Error handling: `app/error.tsx` (segment errors), `app/global-error.tsx` (root failures), `app/not-found.tsx` (404) — all render the shared `ErrorPage` component. Route protection is client-side via `RouteGuard` in the `exam` and `examiner` layouts (no Next.js middleware).

### 8.2 Key modules (`frontend/lib/`)

| Module | Responsibility |
|--------|----------------|
| `api/client.ts` | Core fetch layer: `apiFetch`, `apiFetchEnvelope` (unwraps `{data, meta}`), `apiFetchBlob`; all requests use `credentials: "include"`; parses problem+json into `ApiError`; supports `X-CSRF-Token`, `If-Unmodified-Since`, `Idempotency-Key` headers |
| `api/auth.ts`, `api/examinee.ts`, `api/examiner.ts` | Typed endpoint wrappers per domain |
| `auth/auth-provider.tsx` | React Context: bootstraps CSRF + current user on mount, exposes `loginExaminer`, `enterExaminee`, `logout`, refresh helpers; hooks `useAuth()` / `useRequiredRole(role)` |
| `hooks/use-test-session.ts` | Test-taking orchestration: question loading, answer saving with conflict retry (409 → reload + retry; 403 → CSRF refresh + retry), submit with stable `crypto.randomUUID()` idempotency key |
| `errors/problem.ts` | RFC 7807 parsing, `ApiError`, user-facing message mapping |
| `types/index.ts` | Hand-written DTO types aligned with backend Pydantic schemas (`openapi-typescript` available via `pnpm generate:types`) |

State management is React Context only (no Redux/Zustand/TanStack Query).

### 8.3 Components

- `components/ui/` — shadcn/ui primitives (style: `new-york`): button, card, dialog, alert-dialog, table, tabs, select, radio-group, etc.
- `components/route-guard.tsx` — client-side role/session guard with redirect to `/`.
- `components/status-announcer.tsx` — WCAG live-region provider for screen-reader announcements.
- `components/error-page.tsx` — reusable HTTP error UI (400/401/403/404/500/503).

---

## 9. Testing

### Backend (`backend/tests/`, pytest)

| Layer | Location | Notes |
|-------|----------|-------|
| API contract tests | `tests/test_*.py` | `TestClient` with mocked services; assert envelopes and problem+json shapes |
| Unit tests | `tests/unit/` | Services, guards, repositories, jobs with mocked dependencies |
| Migration tests | `tests/test_migrations.py` | Gated by `RUN_DB_TESTS=1`; requires a real PostgreSQL |

Run: `make backend-test` (root) or `cd backend && pytest`. Dev tooling includes `fakeredis` and `testcontainers[postgres]`.

### Frontend E2E (`frontend/e2e/`, Playwright)

| Spec | Coverage | Requirements |
|------|----------|--------------|
| `accessibility.spec.ts` | axe WCAG 2.1 AA scan, skip-link focus order | None (frontend only) |
| `examinee-flow.spec.ts` | Entry → test → submit → results | `E2E_WITH_API=1` + running backend |
| `examiner-flow.spec.ts` | Login failure + dashboard | `E2E_WITH_API=1` + credentials env vars |

Run: `cd frontend && pnpm test:e2e`. Chromium only; auto-starts the dev server locally. E2E is not part of CI.

### CI (`.github/workflows/ci.yml`)

On push/PR to `main`/`master`: **backend-lint** (ruff), **backend-test** (pytest + Postgres service + Alembic), **frontend-lint** (ESLint + `tsc --noEmit`), **frontend-build** (`pnpm build`). A separate `dependency-review.yml` runs `pip-audit` and `pnpm audit` (non-blocking).

---

## 10. Local Development & Operations

### Quick start

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env.local
make dev-up                      # postgres + redis + api (Docker Compose)
cd frontend && pnpm install && pnpm dev   # frontend on :3000
```

### First-time data setup

```bash
python scripts/bootstrap_examiner.py --username admin --password "ChangeMe123456!"
python scripts/seed_questions.py --count 55 --examiner-username admin
```

### Common commands (Makefile)

| Command | Description |
|---------|-------------|
| `make dev-up` / `make dev-down` | Start / stop the Compose stack |
| `make backend-test` | Run pytest |
| `make backend-lint` | Ruff check + format |
| `make db-migrate` | Alembic upgrade to head |
| `make frontend-dev` / `make frontend-build` | Next.js dev server / production build |

### Docker Compose services (`infra/docker-compose.yml`)

| Service | Image | Port | Notes |
|---------|-------|------|-------|
| `postgres` | `postgres:15-alpine` | 5432 | DB `mcq_platform`, persistent volume, `pg_isready` healthcheck |
| `redis` | `redis:7-alpine` | 6379 | `redis-cli ping` healthcheck |
| `api` | built from `backend/Dockerfile` | 8000 | Hot-reload volume mounts; waits for healthy postgres + redis |

nginx (TLS termination, reverse proxy) is planned but not yet implemented — see `infra/nginx/README.md`. For production deployment details, see [DEPLOYMENT.md](DEPLOYMENT.md).

### API exploration (Postman)

`postman/` contains a ready-made collection (24 requests), a local environment, and the exported OpenAPI spec. After API changes, regenerate with `python backend/scripts/build_postman_collection.py`. A scripted runner exists at `backend/scripts/run_postman_collection.py`.

---

## 11. Conventions

- **Response envelope:** every JSON success response is `{ "data": ..., "meta": { "request_id": "..." } }`; the same ID is echoed in the `X-Request-Id` header.
- **Errors:** always RFC 7807 problem+json; never leak stack traces (unhandled exceptions → generic 500, logged server-side).
- **Soft deletes:** `users` and `questions` use `deleted_at` / `is_deleted` rather than hard deletes (hard deletion only via GDPR erasure and retention purge).
- **Layering rule:** routes never touch the DB directly — always API → service → repository; pure rules live in `domain/` with no I/O.
- **No PII in Redis or logs;** PRN/name encrypted at rest in PostgreSQL.
- **Pagination:** cursor-based for examiner list endpoints.
