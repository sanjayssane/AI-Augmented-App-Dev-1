# Nginx (staging / production)

Phase 6+ deployment placeholder.

## Planned responsibilities

- TLS termination (TLS 1.2+ minimum per PRD §4.2)
- Security headers: CSP, HSTS, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy` (PRD §4.5)
- Reverse proxy:
  - `/api` → FastAPI (`api:8000`)
  - `/` → Next.js frontend (`frontend:3000` or static export)

## Not included in Phase 0

No `nginx.conf` is committed until staging infrastructure is defined.
