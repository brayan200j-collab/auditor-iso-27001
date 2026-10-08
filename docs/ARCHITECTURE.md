# Architecture

Modular monolith with executable dependency rules (CLAUDE.md section 6).

```
Browser ──► Next.js (apps/web)
              │  Server Components → FastAPI with the user's JWT
              │  Client components → /api/backend/* (BFF route handler adds the JWT)
              ▼
           FastAPI (apps/api) ──► Supabase Auth (JWKS)   verify ES256 access tokens
              │                 ──► PostgreSQL + FTS        RLS deny-by-default
              │                 ──► Supabase Storage        private buckets, signed URLs
              │                 ──► PyMuPDF                 extraction per page
              │                 ──► LLMProvider             fake | groq | gemini (dev only)
              └───────────────► Jinja2 + WeasyPrint      PDF report
```

## Backend (`apps/api/src/auditor`)

| Module | Responsibility |
|---|---|
| `shared` | Kernel: `Actor`/`Role`, domain errors, audit vocabulary, ports (UoW, clock, audit, storage), DB base, middleware, error handlers, DI seam |
| `identity` | Token verification, current user, **permission matrix**, users |
| `companies` | Companies and membership |
| `evaluations` | Evaluations, consent, analysis runs, state machine, reviewer assignment |
| `documents` | PDF validation, storage, extraction, chunking, FTS evidence search |
| `checklist` | Versioned checklist (`ISO-01..ISO-30`) |
| `analysis` | AI engine, prompts, citation verification, quotas, pipeline orchestration |
| `review` | Human review (three layers: `ai_findings` → `human_reviews` → `final_findings`) |
| `reports` | PDF report and signed download |
| `feedback` | Validation survey |
| `audit` | `audit_logs` (insert-only) |
| `metrics` | Pilot metrics (read model) |
| `retention` | Retention and purge |

Every module has `domain/`, `application/`, `infrastructure/`, `api/` and optionally `public.py`.

**Rules (import-linter, `apps/api/.importlinter`, run by `make arch`):**
- `domain` imports no framework (no FastAPI, SQLAlchemy, Pydantic, httpx, PyMuPDF…).
- `application` never imports SQLAlchemy, FastAPI, HTTP clients or adapters; it depends on ports.
- `api` and `infrastructure` are independent of each other; `api` contains no SQL.
- A module never imports another module's layers directly — only its `public.py`.
- `shared` does not depend on feature modules.
- Composition happens only in `auditor/container.py` and `auditor/main.py`.
- Cross-module aggregates (`metrics` dashboards, `retention` purge) are read models with plain SQL
  over the tables, so they never import another module's internals (D-037, D-038).

**Dependency injection:** routers declare `Depends(use_case(X))`. The composition root overrides the
`get_resolver` placeholder with a request-scoped resolver that owns one `AsyncSession` per request
(see D-007).

## Frontend (`apps/web/src`)

- `app/` — routes only compose features.
- `features/<name>/` — screens and hooks per feature; other code imports a feature only through `index.ts`.
- `components/ui/` — base design-system components (leaf: no features, API or auth).
- `components/shared/` — shared composite components.
- `lib/api/` — typed client generated from OpenAPI (`schema.d.ts`) + server/client fetchers.
- `lib/auth/` — the only place that talks to Supabase (Auth only).
- `content/es.ts` — every user-facing Spanish string and enum label.

Rules are enforced by dependency-cruiser (`.dependency-cruiser.cjs`) and ESLint (`no-restricted-globals`
for `fetch`, `no-restricted-imports` for `@supabase/*`, `react/no-danger`, `no-explicit-any`, jsx-a11y strict).
