# MCQ Platform — Postman API tests

## What's included

| File | Purpose |
|------|---------|
| `MCQ-Platform-API.postman_collection.json` | All **24** API requests in 7 folders, with test scripts |
| `MCQ-Platform-Local.postman_environment.json` | `baseUrl` and sample examiner credentials |
| `openapi.json` | OpenAPI 3.1 spec (for `/postman:sync` or Spec Hub) |

Your Postman workspace also has:

- **Collection:** `MCQ Online Test Platform API` (UID `55514000-264a72c5-6e87-447c-bd97-afbf07e40848`)
- **Environment:** `MCQ Platform - Local`

## Prerequisites

1. API running at `http://localhost:8000`
2. PostgreSQL and Redis (recommended):

```bash
cd infra
docker compose up -d
```

3. Import into Postman (if you want the full collection locally):
   - **Import** → `postman/MCQ-Platform-API.postman_collection.json`
   - **Import** → `postman/MCQ-Platform-Local.postman_environment.json`
   - Select the **MCQ Platform - Local** environment

## Run all tests in Postman

1. Open collection **MCQ Online Test Platform API** (or the imported copy).
2. Click **Run** (Collection Runner).
3. Choose environment **MCQ Platform - Local**.
4. Click **Run MCQ Online Test Platform API**.

Each request includes tests for expected HTTP status and response time.

## Run from the terminal (without Newman)

```bash
cd backend
python scripts/run_postman_collection.py
```

Regenerate the collection after API changes:

```bash
cd backend
python -c "import json; from app.main import app; d=app.openapi(); d['servers']=[{'url':'http://localhost:8000'}]; open('openapi-export.json','w').write(json.dumps(d,indent=2))"
python scripts/build_postman_collection.py
```

## Authenticated flows

Most examiner/examinee routes return **401** without a session cookie. To test happy paths:

1. Run **Get Csrf Token** (requires Redis).
2. Run **Examiner Login** with valid `examinerEmail` / `examinerPassword` in the environment.
3. Postman stores the session cookie automatically for follow-up requests.

Adjust credentials in the environment to match your seeded database users.
