#!/usr/bin/env bash
# Acceptance run (CLAUDE.md section 24): clean stack, seed, isolation suite and full E2E.
#
# WARNING: wipes the local application database (development data only). Supabase Auth users
# and Storage objects are kept; the seed re-links the development users.
set -euo pipefail
cd "$(dirname "$0")/.."

COMPOSE="docker compose"
API="$COMPOSE run --rm -T api-dev"
PYTHON=""
for candidate in python3 python; do  # skip stubs such as the Windows Store alias
  if "$candidate" --version >/dev/null 2>&1; then PYTHON="$candidate"; break; fi
done
[ -n "$PYTHON" ] || { echo "Python 3 is required" >&2; exit 1; }

step() { printf '\n==> %s\n' "$*"; }

step "1/6 Supabase local"
pnpm exec supabase start >/dev/null
"$PYTHON" scripts/dev_env.py

step "2/6 Clean database (downgrade to empty, upgrade to head)"
$COMPOSE stop api >/dev/null 2>&1 || true
$API uv run alembic downgrade base
$API uv run alembic upgrade head

step "3/6 Seed checklist v1 and development users"
$API uv run python -m auditor.seed

step "4/6 API (deterministic FakeLLMProvider: tests never call a real AI provider)"
# Restore the API with the developer's own .env (e.g. Groq) when the run ends, even on failure.
trap '$COMPOSE up -d --force-recreate api >/dev/null 2>&1 || true' EXIT
LLM_PROVIDER=fake LLM_API_KEY= $COMPOSE up -d --force-recreate --wait api

step "5/6 Isolation and authorization suites"
$API uv run pytest -q -p no:cacheprovider \
  tests/integration/test_isolation.py \
  tests/integration/test_authentication_required.py \
  tests/unit/test_permissions.py

step "6/6 End-to-end (Playwright: full flow, roles, accessibility)"
pnpm --filter @auditor/web e2e

step "Acceptance passed"
