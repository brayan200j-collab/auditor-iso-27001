# Progress

Source of truth for the continuous execution (CLAUDE.md section 0). Read this first when resuming.

| Slice | Content | Status | Date | Commit | Evidence |
|---|---|---|---|---|---|
| S00 | Environment, monorepo scaffold, Makefile, compose + Supabase local, pre-commit, CI, architecture rules, design tokens, base docs | hecho | 2026-10-07 | 8c43518 | `make check` green: 38 api tests, 3 web tests, 17 import contracts |
| S01 | Data model, migrations, RLS deny-by-default + test, seeds (users, checklist ISO-01..30) | hecho | 2026-10-07 | see `git log --grep S01` | `make check` green: 97 api tests (`tests/integration/test_schema.py`: RLS, grants, append-only, reversibility, drift); `make seed` creates 30 criteria + 5 dev users |
| S02 | Identity: JWT, current user, permission matrix, audit_logs; login, logout, recovery, protected routes | pendiente | | | |
| S03 | Companies and users (admin); reviewer assignment | pendiente | | | |
| S04 | Evaluations: create, list, detail, consent, state machine, progress timeline | pendiente | | | |
| S05 | Secure PDF upload: validators, private storage, deletion, upload UI | pendiente | | | |
| S06 | JobRunner + processing_jobs + recovery; PyMuPDF extraction; chunking + FTS; status polling | pendiente | | | |
| S07 | Versioned checklist: administration and versions | pendiente | | | |
| S08 | AI engine: ports, Fake/Groq providers, prompts, FTS evidence, citation verification, quotas, concurrency, 429 | pendiente | | | |
| S09 | Full analysis: chunks → engine → ai_findings → PENDING_REVIEW, resumable | pendiente | | | |
| S10 | Review: queue, three-layer editing, approve/edit/discard, approve/reject evaluation | pendiente | | | |
| S11 | Approved results for the SME, coverage counts, initial improvement plan | pendiente | | | |
| S12 | PDF report and signed-URL download | pendiente | | | |
| S13 | Validation survey | pendiente | | | |
| S14 | Role dashboards, pilot metrics, anonymized mentor view | pendiente | | | |
| S15 | Retention and purge; audited deletion; pilot guide and consent | pendiente | | | |
| S16 | GeminiProvider (dev only) | pendiente | | | |
| S17 | Hardening: headers, rate limiting, security pass, accessibility, performance | pendiente | | | |
| S18 | Full E2E, A/B isolation, production Dockerfiles, docs, blockers retry, final report | pendiente | | | |

## How to resume
1. `make supabase-start && make env` (Supabase local + `.env`).
2. `docker compose build api-dev` if the image is missing.
3. Continue with the first slice that is not `hecho`.
