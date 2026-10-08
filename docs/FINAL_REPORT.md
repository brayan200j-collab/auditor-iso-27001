# Final report — Auditor Virtual MVP

Date: 2026-10-08 · Branch: `mvp` · Specification: `CLAUDE.md` (Prompt Maestro v3)

> **Auditor Virtual ISO/IEC 27001 con IA es una aplicación web de autoevaluación inicial que analiza documentación empresarial mediante inteligencia artificial y la contrasta con un checklist propio alineado con ISO/IEC 27001:2022, utilizando CIS Controls v8.1 y NIST CSF 2.0 como referencias complementarias. Los resultados generados por la IA son revisados y validados por una persona antes de ser presentados a la empresa.**

## 1. Acceptance criterion (section 24)

**Met locally.** `make acceptance` passed on 2026-10-08: clean database (migrations down to empty
and back up), seed, isolation and authorization suites (84 tests), and the full Playwright suite
(21 tests). The E2E flow `e2e/review.spec.ts` covers exactly the required journey with the
synthetic policy PDF: an SME uploads it ("PDF válido · 5 páginas · Texto detectado"), extraction
and AI analysis run, the reviewer sees "30 criterios evaluados: Encontrados / Parciales / Sin
evidencia", edits one finding (with document and page visible) and approves the rest, approves
the evaluation, and only then the SME sees the approved results, downloads the PDF report through
a signed URL and answers the survey. The isolation walker (`tests/integration/test_isolation.py`)
replays **every** OpenAPI operation as company B's SME and as an unassigned reviewer against
company A's resources: all tenant operations answer 403/404, nothing leaks, and A's data is
unchanged.

## 2. What was built

| Area | Delivered |
|---|---|
| Identity and tenancy | Supabase Auth (JWKS ES256), HttpOnly cookies, single permission matrix (Admin, Revisor, PYME, Mentor), company-scoped repositories, generic 404 + `ACCESS_DENIED` audit, RLS deny-by-default |
| Evaluations | creation, versioned consent, explicit state machine (`DRAFT → … → APPROVED/REJECTED`, `FAILED` + retry), progress timeline with polling, reviewer assignment, quotas |
| Documents | streamed upload ≤ 20 MB, signature/MIME/extension checks, ≤ 30 pages counted first, encrypted/corrupt/scanned/active-content rejection, private Storage, audited deletion |
| Pipeline | `processing_jobs` + in-process runner with claim/heartbeat/retries and recovery sweep; PyMuPDF extraction per page; chunking that never crosses pages; Spanish FTS |
| AI engine | provider-agnostic port; `FakeLLMProvider` (deterministic), `GroqProvider` (strict JSON Schema), `GeminiProvider` (dev only); versioned prompts; 3–5 fragments; no call without evidence; one corrective retry; verified citations; quotas, concurrency, 429/backoff; resumable analysis; `llm_calls` without document text |
| Review | immutable `ai_findings` → `human_reviews` → `final_findings`; queue with attention/low confidence first; approve/edit/discard; approve/reject evaluation |
| Results and report | SME sees only approved results: coverage **as counts**, gaps ordered by priority/risk/effort, three-phase initial improvement plan, finding detail; PDF report (Jinja2 autoescape + WeasyPrint, no external resources) generated after approval, private storage, audited signed-URL download |
| Survey and metrics | one survey per approved evaluation; role dashboards with real counts; pilot metrics (technical and value) for admin, anonymized for mentor; "Sin datos aún" instead of invented values; audit-log screen |
| Retention | PDFs and fragments purged `RETENTION_DAYS` (90) after approval by a periodic sweep and an admin endpoint, audited; results and report kept |
| Hardening | per-request nonce CSP, HSTS, security headers, per-session API rate limits, login throttling, axe WCAG 2.1 AA checks, production Dockerfiles (non-root) |
| Docs | README, ARCHITECTURE, DECISIONS (D-001…D-040), SECURITY, DEPLOY, RUNBOOK, PILOT, BACKLOG, PROGRESS |

## 3. How to run and deploy
- Local: see [README](../README.md) (`make supabase-start`, `make env`, `make install`, `make dev`).
- Quality: `make check` · `make e2e` · `make acceptance` · `make docker-build`.
- Deployment (prepared, **not executed**): [DEPLOY.md](DEPLOY.md) — Vercel + Render/Railway +
  Supabase cloud; operations in [RUNBOOK.md](RUNBOOK.md); pilot in [PILOT.md](PILOT.md).

## 4. Slice → evidence

All slices are `hecho`; each commit was made after `make check` passed (one exception, recorded
below). Detailed evidence per slice: [PROGRESS.md](PROGRESS.md).

| Slice | Commit | Evidence (command → result) |
|---|---|---|
| S00 Environment, scaffold, CI | 8c43518 | `make check` green |
| S01 Data model, RLS, seeds | 464730c | `test_schema.py` (RLS, grants, append-only, reversible migrations) |
| S02 Identity and permissions | 58ab327 | `test_permissions.py` walks the full matrix; `test_supabase_auth.py`; e2e auth |
| S03 Companies and users | 39bf14b | Schemathesis contract, auth walker; e2e admin |
| S04 Evaluations and state machine | 438fdb9 | exhaustive transition table + Hypothesis walk; e2e evaluations |
| S05 Secure upload | ea0bc2a | `test_documents_api.py` (all invalid-file cases) |
| S06 Jobs, extraction, FTS | a3a8a40 | `test_pipeline.py` (ISO-07 evidence on page 3, crash recovery) |
| S07 Versioned checklist | a541e25 | `test_checklist_admin.py` |
| S08 AI engine | 7905cbf | `test_ai_engine.py` (golden set, prompt injection, citations, quotas, 429) |
| S09 Full analysis | 1651407 + 2eca2ce | `test_analysis_pipeline.py` (resume without duplicates) |
| S10 Review | dfea3f6 | `test_review_api.py`, `test_review_rules.py`; e2e review |
| S11 Approved results | 329d868 | `test_results_api.py`, `test_results_rules.py` |
| S12 PDF report | 4c8df57 | `test_reports_api.py` (content, signed URL, audit, isolation) |
| S13 Survey | 3fbf411 | `test_feedback_api.py`; `SurveyForm.test.tsx` |
| S14 Dashboards and metrics | 70b0636 | `test_metrics_api.py`, `test_metrics_rules.py`; e2e metrics |
| S15 Retention | 7e44d19 | `test_retention.py`, `test_retention_policy.py` |
| S16 Gemini (dev) | 777b7ec | `test_gemini_provider.py`, `test_config.py` |
| S17 Hardening | da3a4b6 | `test_rate_limits.py`, `csp.test.ts`, e2e `a11y.spec.ts` |
| S18 Isolation, images, docs | see `git log --grep S18` | `test_isolation.py`; `make docker-build` + smoke tests; `make acceptance` passed |

**Final numbers (2026-10-08):** `make check` → 655 backend tests passed, coverage 90 % overall and
90 % on `domain` + `application` (gate 85 %); 49 frontend tests; 17 import contracts kept; no
dependency-cruiser violations; gitleaks, bandit, pip-audit and pnpm audit clean. `make e2e` → 21
passed. `make acceptance` → passed.

Incident: commit 1651407 (S09) was created while 4 tests were failing; fixed in 2eca2ce and every
later commit was chained as `make check && git commit` (PROGRESS.md).

## 5. Default decisions applied
All defaults of section 4 were used (Groq primary, Gemini dev-only, FastAPI background jobs with
`processing_jobs`, PostgreSQL FTS with 3–5 fragments, 90-day retention, Supabase local, 30 own
criteria, mentor on the metrics screen, deployment prepared but not executed). Every additional
decision is in [DECISIONS.md](DECISIONS.md) (40 entries), notably: per-session rate limits with the
`limits` library (D-040), SQL read models for metrics and retention (D-037, D-038), three-phase
improvement plan without promised deadlines (D-034).

## 6. Blockers and real limitations
- **Blockers:** none ([BLOCKERS.md](BLOCKERS.md)).
- Single API instance: job runner, retention sweep and rate limits live in process memory.
- No antivirus (the `FileScanner` port is a no-op); no OCR or DOCX (out of scope, BACKLOG).
- PDF extraction runs in a thread with a timeout, not in an isolated process with OS limits.
- No load or performance test was run; performance work was limited to indexed queries, polling
  with backoff and background processing.
- The free Groq tier allows roughly a few 30-criterion evaluations per day (D-030); enough for a
  2–3 SME pilot, not more.

## 7. Not verified
- **GroqProvider against the real API:** verified on 2026-10-08 with the team's key: the account
  lists `openai/gpt-oss-120b`, and one call with a synthetic fragment returned a finding that
  validates against the strict schema (476 input / 264 output tokens). A full 30-criterion
  analysis and the current free-tier limits were not measured.
- **GeminiProvider:** the documentation site was unreachable from this environment and no key was
  used (D-039).
- **Provider privacy terms:** Groq's data-processing and retention terms have not been reviewed.
- **Cloud deployment:** Vercel, Render/Railway and Supabase cloud were not provisioned.
- **Legal texts:** privacy policy, conditions and consent are drafts (Ley 1581 de 2012) marked
  "revisar con asesor".
- **Normative references:** ISO/IEC 27001:2022, CIS Controls v8.1 and NIST CSF 2.0 identifiers in
  the checklist are `draft` ("referencia por confirmar") and must be confirmed by the team; no
  literal text of the standards is stored.
- **Email delivery:** tested against Supabase local's mail catcher, not a real SMTP sender.
- **Trivy image scans:** configured in CI; not executed locally.

## 8. Connecting real keys (no code changes)
1. Groq (done locally on 2026-10-08): create an API key; set `LLM_PROVIDER=groq`, `LLM_API_KEY`, `LLM_MODEL=openai/gpt-oss-120b`
   in the API environment (locally in `.env`, then restart the API). Run one evaluation with a
   **synthetic** PDF and check `llm_calls` and the metrics screen.
2. Supabase cloud: set `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_PUBLIC_URL`,
   `SUPABASE_JWT_ISSUER`, `SUPABASE_SERVICE_ROLE_KEY` (API) and the `NEXT_PUBLIC_*` values (web),
   following [DEPLOY.md](DEPLOY.md).
3. Set `APP_ENV=pilot`: the API refuses to start with `fake` or `gemini`, with test adapters or
   without the required variables.
4. Complete the pre-pilot checklist in [PILOT.md](PILOT.md) (legal review, provider terms,
   reference confirmation) before processing any real document.
