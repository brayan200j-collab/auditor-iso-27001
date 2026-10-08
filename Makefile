# Auditor Virtual — developer entry points. Run from Git Bash (Windows) or any POSIX shell.
# Backend commands run inside Docker (WeasyPrint needs Linux system libraries).

SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

COMPOSE := docker compose
API := $(COMPOSE) run --rm -T api-dev
WEB := pnpm --filter @auditor/web
SUPABASE := pnpm exec supabase

.PHONY: help install env supabase-start supabase-stop dev dev-api dev-web down migrate seed \
	lint typecheck arch gen-api contract test test-api test-web security check \
	e2e acceptance docker-build fixtures

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'

install: ## Install Node dependencies and build the API dev image
	pnpm install --frozen-lockfile
	$(COMPOSE) build api-dev

supabase-start: ## Start Supabase local (Postgres, Auth, Storage)
	$(SUPABASE) start

supabase-stop: ## Stop Supabase local
	$(SUPABASE) stop

env: ## Generate .env and apps/web/.env.local from Supabase local (random dev passwords)
	python scripts/dev_env.py

migrate: ## Apply database migrations
	$(API) uv run alembic upgrade head

seed: migrate ## Seed checklist v1 and development users (refuses to run in production)
	$(API) uv run python -m auditor.seed

dev-api: ## Run the API (http://localhost:8000)
	$(COMPOSE) up -d --build api

dev-web: ## Run the web app (http://localhost:3000)
	$(WEB) dev

dev: supabase-start env dev-api seed dev-web ## Full local stack

down: ## Stop the API container
	$(COMPOSE) down

# ---------------------------------------------------------------- quality gates
lint: ## 1. Format and lint (ruff, ESLint, Prettier)
	$(API) sh -c "uv run ruff format --check . && uv run ruff check ."
	$(WEB) lint
	$(WEB) format:check

typecheck: ## 2. Types (mypy --strict, tsc --noEmit)
	$(API) uv run mypy
	$(WEB) typecheck

arch: ## 3. Architecture rules (import-linter, dependency-cruiser)
	$(API) uv run lint-imports
	$(WEB) arch:check

gen-api: ## Regenerate the typed TypeScript client from the OpenAPI document
	$(API) uv run python scripts/export_openapi.py
	$(WEB) gen:api

contract: gen-api ## 4. Contract: generated client must be committed and up to date
	@git diff --exit-code -- apps/web/src/lib/api/schema.d.ts \
		|| (echo "The TypeScript API client is outdated: run 'make gen-api' and commit it." && exit 1)
	@test -z "$$(git ls-files --others --exclude-standard apps/web/src/lib/api/schema.d.ts)" \
		|| (echo "schema.d.ts is not committed." && exit 1)

test-api: ## 5a. Backend tests (unit + integration + Schemathesis) with coverage gate
	$(API) sh -c "uv run pytest --cov=auditor --cov-report=term && \
		uv run coverage report --include='*/domain/*,*/application/*' --fail-under=85"

test-web: ## 5b. Frontend tests (Vitest)
	$(WEB) test

test: test-api test-web ## Backend and frontend tests

security: ## 6. Security scanners (gitleaks, bandit, pip-audit, pnpm audit)
	gitleaks git --no-banner --redact .
	for dir in apps/api apps/web/src scripts seeds prompts docs supabase; do \
		gitleaks dir --no-banner --redact --config .gitleaks.toml "$$dir"; done
	$(API) uv run bandit -q -c pyproject.toml -r src
	$(API) sh -c "uv export --format requirements-txt --no-emit-project --all-groups > /tmp/requirements.txt && uv run pip-audit --strict --disable-pip -r /tmp/requirements.txt"
	pnpm audit --audit-level high

check: lint typecheck arch contract test security ## All quality gates, in order

fixtures: ## Generate synthetic PDF fixtures (never real company documents)
	$(API) uv run python -m tests.fixtures.generate

e2e: ## End-to-end tests (Playwright) against the running local stack
	$(WEB) e2e

acceptance: ## Clean stack + seed + full E2E + isolation suite
	bash scripts/acceptance.sh

docker-build: ## Build production images
	docker build -f apps/api/Dockerfile --target runtime -t auditor-api:latest .
	docker build -f apps/web/Dockerfile -t auditor-web:latest 		--build-arg NEXT_PUBLIC_SUPABASE_URL="$${NEXT_PUBLIC_SUPABASE_URL:-http://127.0.0.1:54321}" 		--build-arg NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY="$${NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY:-sb_publishable_build_placeholder}" 		--build-arg NEXT_PUBLIC_API_URL="$${NEXT_PUBLIC_API_URL:-http://127.0.0.1:8000}" 		--build-arg NEXT_PUBLIC_SITE_URL="$${NEXT_PUBLIC_SITE_URL:-http://localhost:3000}" .
