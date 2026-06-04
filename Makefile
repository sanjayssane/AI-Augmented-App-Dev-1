.PHONY: dev-up dev-down dev-logs backend-test backend-lint frontend-lint frontend-build frontend-dev install-backend db-migrate db-downgrade db-revision

COMPOSE_FILE := infra/docker-compose.yml

dev-up:
	docker compose -f $(COMPOSE_FILE) up -d --build

dev-down:
	docker compose -f $(COMPOSE_FILE) down

dev-logs:
	docker compose -f $(COMPOSE_FILE) logs -f

install-backend:
	cd backend && pip install -e ".[dev]"

db-migrate:
	cd backend && alembic upgrade head

db-downgrade:
	cd backend && alembic downgrade -1

db-revision:
	@test -n "$(MSG)" || (echo "Usage: make db-revision MSG='description'" && exit 1)
	cd backend && alembic revision --autogenerate -m "$(MSG)"

backend-test:
	cd backend && pytest tests -v

backend-lint:
	cd backend && ruff check . && ruff format --check .

frontend-lint:
	cd frontend && pnpm lint && pnpm exec tsc --noEmit

frontend-build:
	cd frontend && pnpm build

frontend-dev:
	cd frontend && pnpm dev
