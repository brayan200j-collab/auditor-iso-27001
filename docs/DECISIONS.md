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

## D-019 · Schemathesis configuration
- **Context:** gate 4 runs Schemathesis against the OpenAPI document (`tests/integration/test_contract.py`, all operations, admin token).
- **Decision:** all default checks run except `ignored_auth` (it re-sends our explicit Authorization header and reports a false positive; anonymous access is covered by `test_authentication_required.py`, which walks every operation) and `positive_data_acceptance` (business rules such as "an SME needs a company" legitimately reject schema-valid input with 422).
- **Alternatives:** encode business rules in JSON Schema (not expressible); drop Schemathesis (forbidden).
- **Reason:** keeps every meaningful contract check. Findings already fixed thanks to it: complete `Allow` header on 405, documented 400, non-nullable optional query parameters, NIT pattern in the schema, rejection of undeclared query parameters.

## D-020 · Email links verified with token_hash
- **Context:** Supabase invitation links use the implicit flow (token in the URL fragment, invisible to the server) and PKCE recovery links only work in the browser that requested them.
- **Decision:** custom Supabase email templates (`supabase/templates/*.html`) point to `/auth/confirm?token_hash=…&type=invite|recovery`; the web server calls `verifyOtp`, opens an HttpOnly session and continues to `/restablecer`. The same templates must be configured in Supabase cloud (docs/DEPLOY.md).
- **Alternatives:** client-side fragment handling (needs JS-readable tokens).
- **Reason:** works across browsers and keeps tokens server-side.

## D-021 · Undeclared query parameters are rejected
- **Context:** allowlist input validation (OWASP ASVS V5).
- **Decision:** a global dependency compares the query string with the parameters declared for the operation in the OpenAPI document and answers 422 `VALIDATION_ERROR` for anything else. List filters are declared as individual query parameters (dependency functions) instead of Pydantic query models, which this FastAPI version publishes as a single object parameter.
- **Alternatives:** ignore unknown parameters.
- **Reason:** predictable contract; the generated TypeScript client serializes filters correctly.

## D-022 · Email syntax validation without email-validator
- **Context:** `pydantic.EmailStr` (email-validator) rejects reserved domains such as `.test` and `.local`, used by synthetic development accounts.
- **Decision:** a pragmatic syntax pattern on input; deliverability is proven by the Supabase invitation email itself.
- **Alternatives:** add `pydantic[email]` and special-case test domains.
- **Reason:** one less dependency; real addresses are still validated by delivery.

## D-023 · Reviewer assignment ships with evaluations (S04)
- **Context:** section 23 lists "asignación de revisor" in S03, but there are no evaluations to assign until S04.
- **Decision:** S03 delivers companies and users; the assignment endpoint and UI are delivered and tested in S04.
- **Alternatives:** an assignment table without evaluations.
- **Reason:** vertical slices must be testable end to end.

## D-024 · Evaluation data scope and the public access service
- **Context:** section 8 requires company-scoped repositories and a generic 404 (with an audit entry) for cross-company access.
- **Decision:** evaluation queries require a `DataScope` (all for admins, own company for SMEs, assigned for reviewers) derived from the permission matrix. Other modules load evaluations only through `EvaluationAccess.require` (`auditor.evaluations.public`), which audits `ACCESS_DENIED` when the evaluation exists outside the scope and always answers 404. Lifecycle changes go through `EvaluationLifecycle`, which persists with compare-and-set on the status (concurrent transitions get 409).
- **Alternatives:** per-module ownership checks; database RLS policies for the backend role (the backend bypasses RLS).
- **Reason:** one authorization path that tests can exercise exhaustively.

## D-025 · Multiple PDFs per evaluation and the state machine extensions
- **Context:** section 11 lists the main states; uploading and deleting documents also move an evaluation between DRAFT and RECEIVED, and a rejected evaluation reopens with a new analysis run.
- **Decision:** up to `MAX_DOCUMENTS_PER_EVALUATION` (5) PDFs per run. Extra transitions: RECEIVED→RECEIVED (another upload), RECEIVED→DRAFT (last document deleted), REJECTED→RECEIVED (new PDF opens run N+1), FAILED→EXTRACTING/ANALYZING (retry from the last successful step). `failed_stage` records where a run failed so the timeline can show it.
- **Alternatives:** single document per evaluation.
- **Reason:** SMEs usually keep policies in several short files; the report lists "documentos analizados".

## D-026 · Upload pipeline
- **Context:** section 10 requires streaming reception with a hard 20 MB cap, server-side validation and safe handling of active content.
- **Decision:** multipart upload through the BFF; `BodySizeLimitMiddleware` counts bytes as they arrive and answers 413 beyond 20 MB (+64 KB envelope) before anything is buffered; Starlette spools the file to a temporary file that is closed and deleted after the request. Validation order: sanitized name (no paths, control characters or double extensions) → declared MIME → size → `%PDF-` signature → PyMuPDF inspection in a worker thread with a timeout (encryption, 0 or >30 pages counted before extraction, JavaScript/Launch/embedded files, selectable text) → `FileScanner` hook (no-op) → private storage at `companies/{company}/evaluations/{evaluation}/{document}.pdf`. Rejections are audited; a failed database commit deletes the stored object.
- **Alternatives:** raw-body upload; parsing in a subprocess for strict memory limits.
- **Reason:** standard multipart contract documented in OpenAPI; memory is bounded by the size and page caps. A subprocess sandbox is listed in the backlog.

## D-027 · Configurable sign-in rate limits
- **Context:** the E2E suite signs in dozens of times and hit the per-email limit (which proves the limiter works).
- **Decision:** `AUTH_RATE_LIMIT_PER_IP` and `AUTH_RATE_LIMIT_PER_EMAIL` (server-only) default to 10/min and 5/15 min; only the generated local `.env.local` relaxes them.
- **Alternatives:** disabling the limiter in development.
- **Reason:** production keeps strict defaults without special code paths.

## D-028 · Background jobs run as in-process asyncio tasks
- **Context:** section 4 asks for FastAPI `BackgroundTasks` behind a `JobRunner` port, with `processing_jobs` and a recovery sweep. Jobs must also start without a request (recovery, chained steps).
- **Decision:** `AsyncioJobRunner` (same process, same semantics as BackgroundTasks) executes jobs as asyncio tasks. Jobs are claimed with compare-and-set (QUEUED→RUNNING), send heartbeats, retry transient errors with backoff up to `JOB_MAX_ATTEMPTS`, and fail permanent ones (`PermanentJobError`) immediately; a final failure moves the evaluation to FAILED with a friendly reason. `recover()` runs at startup and every `JOB_SWEEP_INTERVAL_SECONDS`: orphaned QUEUED jobs are resubmitted, stale RUNNING jobs requeued or failed as `INTERRUPTED`.
- **Alternatives:** Celery/Redis (forbidden), FastAPI BackgroundTasks only (cannot run without a request).
- **Reason:** no extra infrastructure; durability comes from the database. Limitation: a single API instance should run the sweeper (documented in RUNBOOK).

## D-029 · Chunking strategy
- **Context:** evidence must stay traceable to document and page.
- **Decision:** chunks never cross pages; numbered headings are detected per line and start a new chunk (their text becomes the chunk's `section`); sentences are packed up to ~900 characters (hard cap 1200) with ~150 characters of overlap. PostgreSQL computes the `spanish` tsvector in a generated column.
- **Alternatives:** fixed-size windows; embeddings (out of scope).
- **Reason:** predictable, testable (property test), and good enough for keyword FTS.

## D-030 · Groq adapter verified against the official documentation (2026-10-07)
- **Context:** section 4 asks to confirm the model name, structured output support and limits before implementing.
- **Decision:** `openai/gpt-oss-120b` supports `response_format.json_schema` with `strict: true` (constrained decoding; every property required and `additionalProperties: false`, so the Pydantic schema is inlined and closed by `strict_json_schema()`). Free tier: 30 RPM, 1,000 RPD, 8,000 TPM, 200,000 TPD; 429 responses carry `retry-after`. Pydantic validation still runs on every answer, with one retry that includes the validation error. Defaults: `LLM_MAX_CONCURRENCY=2`, `MAX_TOKENS_PER_CALL=2000`, `reasoning_effort=low` (configurable through `LLM_REASONING_EFFORT`).
- **Alternatives:** JSON mode without schema (fallback not needed).
- **Reason:** guaranteed schema conformance. With ~1,500 tokens per criterion, a 30-criterion evaluation takes several minutes on the free tier (about 4 evaluations per day); enough for a 2–3 SME pilot. Not verified with a real key in this environment.

## D-031 · Data minimization and citation design
- **Context:** section 9.1: send the minimum, never show invented citations.
- **Decision:** the model receives at most `EVIDENCE_TOP_K` delimited fragments, documents are named "Documento N" (never the file name), and no company or user data. The model cites by fragment id; document and page are taken from the real fragment and the quote is verified against its text (case, whitespace and typographic quotes normalized, 15–300 characters). Unknown fragment ids are discarded and flagged; unverified quotes are kept but flagged. Document text that tries to open or close the delimiters is neutralized. `llm_calls.structured_result` stores status, confidence and fragment ids, never quotes.
- **Alternatives:** let the model report document and page.
- **Reason:** traceability cannot depend on the model's honesty.

## D-032 · Findings without a model call and the deterministic test double
- **Context:** criteria without relevant fragments are classified without the AI; tests and CI never call a real provider.
- **Decision:** without fragments the finding is NO_DOCUMENTARY_EVIDENCE with `confidence = NULL` (no model estimated it) and checklist defaults for priority/risk/effort. `FakeLLMProvider` applies transparent keyword rules on the most relevant fragment (hedges such as "en elaboración" ⇒ PARTIAL) and quotes real sentences; a golden set over the synthetic policy pins its behavior.
- **Alternatives:** random or canned fake answers.
- **Reason:** deterministic, explainable local runs and E2E tests.

## D-033 · Human review rules and the three-layer model
- **Context:** section 14: the AI result is never overwritten and the company only sees reviewed results.
- **Decision:** `ai_findings` stay immutable; every reviewer action appends a `human_reviews` row (previous and new values) and upserts one `final_findings` row per finding. Approve copies the AI values and only verified citations; edit may change status, gap, recommendation, priority, risk and effort (editing to NO_DOCUMENTARY_EVIDENCE drops evidence); discard needs a comment of at least 10 characters and leaves classification fields NULL (migration 0003, check constraint `ck_final_findings_classified_unless_discarded`). Findings without a classification (model error) can only be edited. The evaluation is approved only when no finding is pending; rejection needs a reason of at least 10 characters. Approval exposes an `after_approval` hook used by the report step (S12). The queue orders pending findings needing attention first, then lowest confidence.
- **Alternatives:** editing `ai_findings` in place; a single findings table with a status column.
- **Reason:** full traceability of who changed what, and the SME can never receive an unreviewed AI result.

## D-034 · Approved results, coverage counts and the initial improvement plan
- **Context:** section 15: the SME sees only approved results; coverage only as counts.
- **Decision:** `GET /evaluations/{id}/findings` returns final findings only when the evaluation is APPROVED (409 `CONFLICT` before that, no data). Discarded findings are not shown; coverage reports found/partial/no-evidence counts out of the checklist total plus "no incluidos tras la revisión humana". No confidence or AI-only fields reach the company. Gaps (partial and no evidence) use the shared ordering (priority → risk → effort); the plan groups them in three phases by priority: critical/high "Abordar primero", medium "A continuación", low "Más adelante". No time frames are promised.
- **Alternatives:** time-boxed phases (30/60/90 days); showing discarded criteria.
- **Reason:** honest, actionable order without inventing deadlines; same use case feeds the PDF report.

## D-035 · PDF report generation and download
- **Context:** section 15: report only after approval, private storage, signed URL, audit.
- **Decision:** after the approval commits, `ScheduleReport` queues a REPORT job (`ApproveEvaluation.after_approval`); `GenerateReport` builds the content from `GetApprovedResults` (reviewed findings only), renders Jinja2 (autoescape) → WeasyPrint with a URL fetcher that refuses every external resource, stores it at a system path in the private `reports` bucket and records `REPORT_GENERATED`. It is idempotent per analysis run; reviewers/admins can request it again (e.g. after a failure) with `POST /evaluations/{id}/report`, which returns 409 before approval. `GET /reports/{id}/download` checks scope, records `REPORT_DOWNLOADED` and returns a signed URL valid for `SIGNED_URL_TTL_SECONDS`; storage paths never reach the browser.
- **Alternatives:** synchronous generation inside the approval request; streaming the PDF through the API.
- **Reason:** approval stays fast and never fails because of rendering; downloads stay auditable without proxying files.

## D-036 · Validation survey
- **Context:** section 15: one survey per approved evaluation to measure pilot value.
- **Decision:** `POST /feedback` (SME of the owning company only) accepts four 1–5 scales (usefulness, ease of use, trust, willingness to use), actionable recommendations (yes/no), estimated manual hours and hours using the system (0–1000, one decimal), willingness to pay (yes/maybe/no) and optional comments (≤ 2000). It returns 409 before approval and when an answer already exists (unique per evaluation); each answer is audited as `FEEDBACK_SUBMITTED`. The form accepts comma decimals and the server action validates again with the same schema.
- **Alternatives:** free-text time estimates; allowing edits after submission.
- **Reason:** comparable numbers for the pilot metrics (S14) and a single, unambiguous answer per evaluation.

## D-037 · Dashboards, pilot metrics and the mentor view
- **Context:** sections 18–19: real dashboard cards per role; technical and value metrics; the mentor sees only anonymized metrics on the same screen.
- **Decision:** a read model in the metrics module (`SqlMetricsReader`) aggregates with plain SQL over the tables, so it never imports other modules' internals. `GET /dashboard` counts active, pending review, approved, processed documents and critical/high gaps of approved evaluations, scoped by role (SME: own company, reviewer: assigned, admin: all; mentor 403). `GET /metrics` (admin and mentor) returns aggregates only — processed-PDF ratio, extraction errors, failures, average analysis time, AI calls, tokens, reviewer modifications, access denials, and survey averages — with `null` when there is no data ("Sin datos aún"). The mentor lands on Métricas with an "anonimizada" notice. The admin audit-log screen (filters by action and outcome, Spanish labels) was added as part of this slice.
- **Alternatives:** each module exposing its own counters through `public.py`; materialized views.
- **Reason:** one cheap, auditable query set for a 2–3 SME pilot without coupling modules.

## D-038 · Retention and purge
- **Context:** sections 4 and 9: delete original PDFs and fragments 90 days after approval (configurable), keep final findings and report, with an audit trail.
- **Decision:** `PurgeExpiredDocuments` (retention module) finds unpurged documents of evaluations approved before `now - RETENTION_DAYS`, deletes the Storage object (tolerating already-missing objects), deletes the fragments, marks the document `PURGED` without storage path, and audits `RETENTION_PURGED` per evaluation, committing each evaluation separately. It runs at startup and every `RETENTION_SWEEP_INTERVAL_SECONDS` (default 6 h), and on demand through `POST /retention/purge` (new `MANAGE_RETENTION` permission, admin only). The data adapter uses plain SQL so the module does not import documents internals. Results expose `documents_retained_until`, shown to the SME. The consent text states 90 days; a different period requires a new consent version.
- **Alternatives:** database cron (pg_cron) or deleting whole evaluations.
- **Reason:** works the same locally and in the cloud, keeps what the company needs (results and report) and leaves a trace of every deletion.

## D-039 · GeminiProvider for development only
- **Context:** section 4: Gemini as a backup adapter only for development with synthetic documents (its free tier may use content to improve Google products); no automatic failover.
- **Decision:** `GeminiProvider` calls `v1beta/models/{model}:generateContent` with the `x-goog-api-key` header, `systemInstruction`, one user turn and `generationConfig` = `responseMimeType: application/json` + `responseJsonSchema` (the same closed schema used for Groq), `maxOutputTokens` and low temperature; 429/5xx/4xx map to the same errors as Groq, so retries, quotas and the single corrective retry apply unchanged. It is selected only with `LLM_PROVIDER=gemini` and configuration refuses it in `pilot`/`production` even if listed in `LLM_PROVIDERS_ALLOWED_FOR_REAL_DATA`.
- **Not verified:** the official documentation site was unreachable from this environment and no real key was used; field names follow the documented REST API at the time of writing. Pydantic validation and the corrective retry protect against schema-support differences.
- **Reason:** a second provider for local experiments without coupling business logic to any provider.

## D-040 · Hardening: CSP with nonce, per-session API rate limits, accessibility gate
- **Context:** section 9 and S17: restrictive CSP, rate limiting on sensitive operations, accessibility (WCAG 2.1 AA).
- **Decision:** the Next.js proxy creates a nonce per request and sends a CSP with `'nonce-…' 'strict-dynamic'` (no inline scripts; `'unsafe-eval'` and `ws:` only in development); the root layout reads the request so every page is dynamic and gets its nonce; HSTS in production. The API enforces limits with a FastAPI dependency over the `limits` library (slowapi's engine): general limit on every router, stricter ones on upload, start/retry and report download, keyed by a hash of the bearer token because all traffic arrives from the Next.js server's IP; 429 `RATE_LIMITED` with `Retry-After`. In-memory storage protects a single instance. Playwright runs axe (WCAG 2.1 A/AA) on every role's screens and on the review, results, survey and detail pages.
- **Alternatives:** slowapi decorators (need a module-level limiter bound before settings exist); IP-based keys (would throttle all users together); static CSP with `'unsafe-inline'`.
- **Reason:** strong script policy without breaking Next.js, fair per-user limits, and accessibility checked continuously instead of once.

## D-041 · Lock down `alembic_version` and default privileges (Supabase cloud)
- **Context:** the first cloud migration showed that Supabase cloud grants new `public` tables to `anon`/`authenticated` by default; `alembic_version` exists before 0001 runs, so it stayed readable and writable through the Data API with the publishable key.
- **Decision:** migration 0004 enables RLS on `alembic_version`, revokes its grants and removes the default table/sequence grants for `anon`/`authenticated` in `public`. `test_schema.py` checks it. Verified in the cloud project: 0 grants, RLS on every table, REST answers 401 "permission denied".
- **Reason:** deny-by-default must not depend on the hosting defaults.

## D-042 · Direct PDF uploads to the API with short-lived tickets
- **Context:** Vercel limits function request bodies to 4.5 MB, below the 20 MB PDFs the product accepts; uploads through the BFF returned 413. The session token lives in an HttpOnly cookie and must not be exposed to JavaScript.
- **Decision:** the BFF obtains `POST /evaluations/{id}/documents/upload-ticket` (same permission and rate limit as uploading): an HMAC-SHA256 ticket bound to the user and the evaluation, valid 5 minutes. The browser then sends the multipart PDF straight to the API with `X-Upload-Ticket`; the upload endpoint accepts either the bearer token or a valid ticket and still applies every validation and state rule. The web CSP allows `connect-src` to the API origin; the API CORS allows the `X-Upload-Ticket` header and, optionally, `ALLOWED_ORIGIN_REGEX` for the host's preview domains. `UPLOAD_TICKET_SECRET` is optional (random per process; single instance). Route `DELETE /documents/{document_id}` is constrained to UUIDs so `/documents/upload-ticket` answers 405 for other methods.
- **Alternatives:** returning the access token to the browser; signed upload URLs straight to Storage (validation would run after storing, and the spec requires uploads to go through the backend).
- **Reason:** 20 MB uploads on serverless hosting without weakening the session model.
