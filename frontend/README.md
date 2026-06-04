# MCQ Platform Frontend

Next.js 16 scaffold (Phase 0). UX reference: [../SampleUI/](../SampleUI/) — do not copy mock implementations.

## Setup

```bash
pnpm install
cp .env.example .env.local
pnpm dev
```

Commit `pnpm-lock.yaml` after first `pnpm install` for reproducible CI.

## Routes (stubs)

| Path | Module |
|------|--------|
| `/` | Landing |
| `/exam/test` | Test interface |
| `/exam/results` | Results & review |
| `/examiner/dashboard` | Examiner dashboard |

Phase 5 will add `/examiner/sessions/[id]` and `/examiner/settings`.
