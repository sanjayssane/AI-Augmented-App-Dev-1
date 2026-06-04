# API client (Phase 5)

Typed fetch wrapper with:

- `credentials: 'include'` for HttpOnly session cookies
- `X-CSRF-Token` header on state-changing requests
- Base URL from `NEXT_PUBLIC_API_BASE_URL`

See `client.ts` for the scaffold stub.
