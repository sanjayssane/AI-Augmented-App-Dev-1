# API Client

Typed wrappers for FastAPI `/api/v1` endpoints.

| Module | File |
|--------|------|
| Core fetch | `client.ts` — cookies, CSRF, concurrency headers, blob downloads |
| Auth | `auth.ts` |
| Examinee | `examinee.ts` |
| Examiner | `examiner.ts` |

Types live in `lib/types/index.ts`. Regenerate from OpenAPI with `npm run generate:types`.
