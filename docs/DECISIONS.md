# Decisions log

Format: context · decision · alternatives · reason. Newest last.

## D-001 · Supabase local through a pinned npm CLI
- **Context:** the Supabase CLI was not installed globally; a Supabase local stack from a previous attempt was already running with an empty database.
- **Decision:** add `supabase@2.120.0` as a root devDependency and run it with `pnpm exec supabase`. `supabase/config.toml` is versioned with `project_id = "pagina_web_iso27001"`.
- **Alternatives:** plain PostgreSQL + development adapters (allowed by section 4), global CLI install.
- **Reason:** keeps the default decision of section 4 (real Supabase Auth/Storage/Postgres locally) with a reproducible, version-pinned CLI.

## D-002 · Backend tooling runs in Docker
- **Context:** the host is Windows; WeasyPrint needs Pango/HarfBuzz system libraries that are not available there.
- **Decision:** lint, types, tests, migrations and seeds of the API run in the `api-dev` image (`apps/api/Dockerfile`, target `dev`) attached to the Supabase Docker network. CI does the same.
- **Alternatives:** native Python with GTK runtime; skipping PDF tests on Windows (forbidden by section 0).
- **Reason:** one Linux environment for local and CI, identical to production.

## D-003 · Node 24 on the developer host
- **Context:** section 0 asks for Node 22 LTS; the host has Node 24.
- **Decision:** `engines.node >= 22`; CI pins Node 22.
- **Alternatives:** install Node 22 with a version manager.
- **Reason:** no feature used requires 24; CI validates the requested LTS.

## D-004 · Dependencies beyond the stack table
- **Context:** section 5 asks for an entry for any extra dependency.
- **Decision:** `python-multipart` (required by FastAPI for multipart uploads), `pyyaml` (parse `seeds/checklist_v1.yaml`), `types-pyyaml` (typing), `eslint-plugin-jsx-a11y` (accessibility lint rules), `class-variance-authority`, `clsx`, `tailwind-merge`, `lucide-react`, `@radix-ui/react-slot` (shadcn/ui building blocks), `vite-tsconfig-paths`, `@vitejs/plugin-react`, `jsdom` (Vitest), `prettier-plugin-tailwindcss` (class ordering), `supabase` (CLI, dev only).
- **Alternatives:** JSON instead of YAML for the checklist seed (section 6 names a `.yaml` file).
- **Reason:** each one is required by a tool already in the stack or by an explicit file format.

## D-005 · shadcn/ui components are vendored by hand
- **Context:** the shadcn CLI is interactive and needs network access to its registry.
- **Decision:** components in `apps/web/src/components/ui` follow shadcn/ui conventions (cva variants, `cn` helper, Radix `Slot`) but are written directly in the repository.
- **Alternatives:** run the CLI.
- **Reason:** same result, reviewable code, no runtime dependency on the registry.

## D-006 · Cross-module communication through `public.py`
- **Context:** section 6 requires modules to talk only through public interfaces, enforced by tools.
- **Decision:** each backend module may expose `auditor/<module>/public.py` (DTOs + ports). import-linter forbids importing another module's `domain`, `application`, `infrastructure` or `api` packages directly. Adapters between modules are wired only in `auditor/container.py`. `Role` and `Actor` live in the shared kernel (`auditor.shared.domain.actor`); the permission matrix lives in `identity`.
- **Alternatives:** one shared repository layer; event bus.
- **Reason:** simplest structure that import-linter can verify.

## D-007 · Dependency-injection seam for routers
- **Context:** routers must only call use cases and must not import infrastructure.
- **Decision:** `auditor.shared.api.dependencies.get_resolver` is a placeholder overridden by the composition root (`app.dependency_overrides`). Routers declare `Depends(use_case(SomeUseCase))`; the request-scoped resolver builds the use case with a per-request `AsyncSession`.
- **Alternatives:** module-level singletons; a DI framework.
- **Reason:** native FastAPI mechanism, no globals, one session per request, easy test overrides.

## D-008 · Test-only token verifier
- **Context:** hundreds of authorization tests need tokens for users that change per test.
- **Decision:** `AUTH_PROVIDER=test` enables an HS256 verifier, accepted only when `APP_ENV=test` (startup fails otherwise). Real Supabase tokens (ES256 via JWKS) are verified in a dedicated integration test and in the E2E suite.
- **Alternatives:** create a Supabase Auth user per test.
- **Reason:** fast, deterministic tests while the production path is still exercised end to end.

## D-009 · Next.js 16 Cache Components disabled
- **Context:** `create-next-app` 16.4 enables `cacheComponents` and `partialPrefetching`. With them, every cookie read must sit behind `<Suspense>` and caches must be reasoned about per user.
- **Decision:** disable both; all authenticated pages render dynamically per request.
- **Alternatives:** adopt `use cache: private` patterns.
- **Reason:** every page shows per-user, per-company data; caching adds risk (cross-tenant leakage) without benefit for a 2–3 SME pilot.

## D-010 · Backend-for-frontend route for client-side calls
- **Context:** TanStack Query polling, mutations and uploads run in the browser, but the access token must not be handled by client JavaScript.
- **Decision:** Server Components call FastAPI directly with the user's JWT. Client components call the same-origin route handler `/api/backend/...`, which reads the Supabase session server-side, attaches the bearer token and forwards to FastAPI (`/api/v1/...` paths only).
- **Alternatives:** expose the token to the browser and call FastAPI cross-origin.
- **Reason:** smaller attack surface; CORS stays strict.

## D-011 · Dedicated test database
- **Context:** integration tests need a real PostgreSQL with the `anon` and `authenticated` roles (RLS test).
- **Decision:** tests use the `auditor_test` database inside the Supabase local cluster (created automatically by the test suite); the schema is rebuilt with Alembic at the start of each run.
- **Alternatives:** separate Postgres container (lacks Supabase roles).
- **Reason:** same engine version and roles as the real database, without touching development data.

## D-012 · Supabase Auth hardening
- **Context:** accounts are created by an administrator; the public must not sign up.
- **Decision:** `[auth].enable_signup = false`, minimum password length 12 with lower/upper/digit requirements, `auto_expose_new_tables = false`, private buckets `documents` and `reports` (PDF only, 20 MiB). Email+password sign-in remains enabled.
- **Alternatives:** keep CLI defaults.
- **Reason:** security is priority 1.

## D-013 · Audit exception for GHSA-vfj7-8cjw-p6xm (braces)
- **Context:** `pnpm audit` reports a high-severity DoS (deeply nested brace patterns) in `braces@3.0.3`. No patched version exists. The only path is `eslint-config-next → @next/eslint-plugin-next → fast-glob → micromatch → braces` (devDependency, lint time only).
- **Decision:** ignore exactly this GHSA in `pnpm-workspace.yaml` (`auditConfig.ignoreGhsas`); the audit threshold stays at `high`.
- **Alternatives:** lower the threshold (forbidden); drop `eslint-config-next` (loses Next.js lint rules).
- **Reason:** the vulnerable code never ships to production and only receives glob patterns written by the team. Remove the exception as soon as a patched release exists (Dependabot weekly).

## D-014 · Development data lives behind explicit seed targets
- **Context:** the checklist must exist in every environment, while development users must never exist in pilot/production.
- **Decision:** `python -m auditor.seed checklist` runs anywhere and is idempotent; `python -m auditor.seed users` refuses to run unless `APP_ENV` is local/test. Dev users are created in Supabase Auth with passwords read from `SEED_*` variables (random per machine via `make env`); companies are synthetic ("Empresa de prueba A/B S.A.S.").
- **Alternatives:** SQL seed file; hardcoded demo accounts (forbidden by section 9).
- **Reason:** no credentials in code or UI; same code path as real accounts.

## D-015 · Database-level integrity guards
- **Context:** `ai_findings` must stay immutable, `audit_logs` insert-only, published checklists immutable.
- **Decision:** triggers reject UPDATE/DELETE on `audit_logs`, `ai_findings`, `human_reviews`, `llm_calls`, and any change to published checklist versions or their items. RLS is enabled on every table with no policies and all grants revoked from `anon`/`authenticated`.
- **Alternatives:** application-only enforcement.
- **Reason:** defense in depth; the guarantees hold even for code paths written later or manual SQL.

## D-016 · Login and recovery rate limiting in the web server
- **Context:** sign-in happens in a Server Action, so Supabase Auth sees the Next.js server IP for every user and its per-IP limit would be shared by everyone.
- **Decision:** the web server applies its own fixed-window limiter before calling Supabase: 10 attempts/minute per client IP and 5 per 15 minutes per email, for login and recovery (`src/lib/rate-limit.ts`). Recovery answers identically whether or not the account exists.
- **Alternatives:** route sign-in through FastAPI; shared Redis limiter (out of scope).
- **Reason:** keeps HttpOnly cookies and server-side auth. Limitation: the store is per instance; a multi-instance deployment needs a shared store (documented in SECURITY.md).

## D-017 · Reviewer scope for approved results is "assigned"
- **Context:** section 7 grants reviewers "ver resultados aprobados y descargar informe" without specifying scope, while they only see their assigned evaluations.
- **Decision:** reviewers can view approved results and download reports only for evaluations assigned to them; administrators see all.
- **Alternatives:** all approved results for any reviewer.
- **Reason:** least privilege, consistent with "Ver evaluaciones: solo asignadas".

## D-018 · Session cookies are HttpOnly; Supabase runs only on the server
- **Context:** section 6 asks for Supabase Auth with `@supabase/ssr` cookie sessions and section 9 for HttpOnly cookies.
- **Decision:** sign-in, sign-out, recovery and password update are Server Actions/route handlers; the Supabase client is created only on the server with `cookieOptions.httpOnly = true`. `proxy.ts` refreshes the session and redirects anonymous visitors from `/app`. Unknown or inactive profiles are signed out immediately after login.
- **Alternatives:** browser Supabase client (requires JS-readable cookies).
- **Reason:** the access token is never exposed to browser JavaScript.
