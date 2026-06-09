# MCQ Platform Frontend

Next.js 16 production UI wired to the FastAPI backend. UX reference: [../SampleUI/](../SampleUI/).

## Setup

```bash
npm install
cp .env.example .env.local
npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1` in `.env.local`.

Backend must allow `http://localhost:3000` in `CORS_ORIGINS`.

## Routes

| Path | Description |
|------|-------------|
| `/` | Landing — examinee entry & examiner login |
| `/exam/test` | 50-question MCQ test (ACTIVE session) |
| `/exam/results` | Score summary & answer review |
| `/examiner/dashboard` | Question bank CRUD & results |
| `/examiner/sessions/[id]` | Session drill-down |
| `/examiner/settings` | Admin settings, examiner provisioning, GDPR erasure |

## E2E Tests

```bash
# Accessibility only (no backend)
npm run test:e2e -- e2e/accessibility.spec.ts

# Full flows (backend + seeded questions required)
E2E_WITH_API=1 E2E_EXAMINER_USER=admin E2E_EXAMINER_PASSWORD=ChangeMe123456! npm run test:e2e
```

## API Integration

- Cookie sessions (`credentials: include`)
- CSRF token from `GET /auth/csrf` on bootstrap
- RFC 7807 error handling in `lib/errors/problem.ts`
