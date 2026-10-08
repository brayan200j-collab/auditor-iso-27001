# Progress

Source of truth for the continuous execution (CLAUDE.md section 0). Read this first when resuming.

| Slice | Content | Status | Date | Commit | Evidence |
|---|---|---|---|---|---|
| S00 | Environment, monorepo scaffold, Makefile, compose + Supabase local, pre-commit, CI, architecture rules, design tokens, base docs | hecho | 2026-10-07 | 8c43518 | `make check` green: 38 api tests, 3 web tests, 17 import contracts |
| S01 | Data model, migrations, RLS deny-by-default + test, seeds (users, checklist ISO-01..30) | hecho | 2026-10-07 | 464730c | `make check` green: 97 api tests (`tests/integration/test_schema.py`: RLS, grants, append-only, reversibility, drift); `make seed` creates 30 criteria + 5 dev users |
| S02 | Identity: JWT, current user, permission matrix, audit_logs; login, logout, recovery, protected routes | hecho | 2026-10-07 | 58ab327 | `make check` green (188 api, 15 web tests; `tests/unit/test_permissions.py` walks the full matrix; `tests/integration/test_supabase_auth.py` verifies a real ES256 token via JWKS); `pnpm --filter @auditor/web e2e` auth.spec: 5 passed |
| S03 | Companies and users (admin); reviewer assignment | hecho | 2026-10-07 | 39bf14b | `make check` green (209 api tests incl. Schemathesis contract and auth walker); e2e `admin.spec.ts` (invite via email link, set password, deactivate): 2 passed. Reviewer assignment moved to S04 (D-023) |
| S04 | Evaluations: create, list, detail, consent, state machine, progress timeline | hecho | 2026-10-07 | 438fdb9 | `make check` green (497 api tests incl. exhaustive state-machine table and Hypothesis walk; scoped listing, quota, consent, assignment, audited cross-company 404); e2e evaluations.spec: 2 passed |
| S05 | Secure PDF upload: validators, private storage, deletion, upload UI | hecho | 2026-10-07 | ea0bc2a | `make check` green (`tests/integration/test_documents_api.py`: fake MIME/extension, corrupt, encrypted, scanned, >30 pages, >20 MB streaming cut-off, dangerous names, JavaScript, attachments, tenancy, deletion, new run after rejection); e2e documents.spec on Supabase Storage: 2 passed (11/11 overall) |
| S06 | JobRunner + processing_jobs + recovery; PyMuPDF extraction; chunking + FTS; status polling | hecho | 2026-10-07 | a3a8a40 | `make check` green (560 api tests; `tests/integration/test_pipeline.py`: extraction, Spanish FTS finds ISO-07 evidence on page 3, idempotency, permanent failure + retry, crash recovery; chunking property test); e2e 12/12 incl. live timeline to "Analizando" |
| S07 | Versioned checklist: administration and versions | hecho | 2026-10-07 | a541e25 | `make check` green (`tests/integration/test_checklist_admin.py`: draft copy, single draft, item edit with validation, publish, published versions immutable, admin-only); e2e checklist.spec: 1 passed |
| S08 | AI engine: ports, Fake/Groq providers, prompts, FTS evidence, citation verification, quotas, concurrency, 429 | hecho | 2026-10-07 | 7905cbf | `make check` green (587 api tests; `tests/integration/test_ai_engine.py`: golden set, verified citations with page, no call without evidence, invalid output + retry, invented quotes/fragments flagged, prompt-injection PDF, quota, no document text in llm_calls; `tests/unit/test_ai_engine_units.py`: strict schema, 429/backoff, Groq adapter on a mock transport) |
| S09 | Full analysis: chunks → engine → ai_findings → PENDING_REVIEW, resumable | hecho | 2026-10-07 | see `git log --grep S09` | `make check` green (`tests/integration/test_analysis_pipeline.py`: 30 findings → PENDING_REVIEW, immutable ai_findings, outage mid-analysis then resume without duplicates, quota → FAILED/QUOTA_EXCEEDED); e2e 13/13 incl. upload → extraction → AI → "Revisión humana" |
| S10 | Review: queue, three-layer editing, approve/edit/discard, approve/reject evaluation | hecho | 2026-10-07 | see `git log --grep S10` | `make check` green (`tests/unit/test_review_rules.py`, `tests/integration/test_review_api.py`: approve/edit/discard, verified-only evidence, history, pending blocks approval, reject reason, locked after decision, scope); web `review-display.test.tsx`; e2e review.spec: reviewer edits one finding, approves 29, approves the evaluation |
| S11 | Approved results for the SME, coverage counts, initial improvement plan | hecho | 2026-10-07 | see `git log --grep S11` | `make check` green (`tests/unit/test_results_rules.py`; `tests/integration/test_results_api.py`: hidden until approval, counts, ordered gaps, plan phases, no unverified quotes, scope); web `results-display.test.tsx`; e2e review.spec continues to the SME results and finding detail |
| S12 | PDF report and signed-URL download | hecho | 2026-10-07 | see `git log --grep S12` | `make check` green (`tests/integration/test_reports_api.py`: no report before approval (409), approval generates the PDF with counts, plan, ISO-07 page 3, reviewer notes, disclaimer and privacy note and without percentages or confidence; signed URL + audit; other company 404, mentor 403; idempotent per run); e2e review.spec downloads `informe-autoevaluacion-inicial.pdf` from Supabase Storage |
| S13 | Validation survey | pendiente | | | |
| S14 | Role dashboards, pilot metrics, anonymized mentor view | pendiente | | | |
| S15 | Retention and purge; audited deletion; pilot guide and consent | pendiente | | | |
| S16 | GeminiProvider (dev only) | pendiente | | | |
| S17 | Hardening: headers, rate limiting, security pass, accessibility, performance | pendiente | | | |
| S18 | Full E2E, A/B isolation, production Dockerfiles, docs, blockers retry, final report | pendiente | | | |

## Incidents
- 2026-10-07: commit 1651407 (S09) was created while `make check` had 4 failing tests (S06/S08 tests still expected the pipeline to stop at ANALYZING). Fixed in the following commit; commits are now chained as `make check && git commit`.

## How to resume
1. `make supabase-start && make env` (Supabase local + `.env`).
2. `docker compose build api-dev` if the image is missing.
3. Continue with the first slice that is not `hecho`.
