# Auditor Virtual

> **Auditor Virtual ISO/IEC 27001 con IA es una aplicación web de autoevaluación inicial que analiza documentación empresarial mediante inteligencia artificial y la contrasta con un checklist propio alineado con ISO/IEC 27001:2022, utilizando CIS Controls v8.1 y NIST CSF 2.0 como referencias complementarias. Los resultados generados por la IA son revisados y validados por una persona antes de ser presentados a la empresa.**

Este resultado corresponde a una autoevaluación inicial y no constituye una certificación ISO/IEC 27001 ni reemplaza una auditoría realizada por un organismo acreditado.

Academic project (Electiva Emprendimiento en TIC, Universidad Santiago de Cali) for SMEs in Valle
del Cauca. Pilot with 2–3 SMEs, no billing, free or low-cost infrastructure.

## What it does

`PDF ≤ 30 pages → extraction → own checklist (ISO-01…ISO-30) → AI → traceable evidence → human review → PDF report`

- **SME (PYME):** creates an evaluation, accepts the versioned consent, uploads PDFs, follows the
  progress, sees only **approved** results (coverage as counts, prioritized gaps, initial
  improvement plan), downloads the report and answers the validation survey.
- **Reviewer:** queue with low-confidence findings first, evidence with document and page
  (unverified citations flagged), approve / edit / discard, approve or reject the evaluation.
- **Admin:** companies, users, reviewer assignment, versioned checklist, audit log, pilot metrics.
- **Mentor:** anonymized pilot metrics only.

The AI receives only 3–5 relevant fragments per criterion, never the full PDF or company data;
its output is schema-validated, citations are verified against the real text, and nothing reaches
the company without human review. El MVP utiliza un proveedor de inteligencia artificial con nivel
gratuito, sujeto a límites de solicitudes y consumo.

## Stack

Next.js (App Router, TypeScript strict, Tailwind, TanStack Query) · FastAPI (Python 3.12,
SQLAlchemy async, Pydantic v2) · Supabase (Postgres + RLS + full-text search, Auth, private
Storage) · PyMuPDF · Jinja2 + WeasyPrint · GroqCloud (`openai/gpt-oss-120b`, structured outputs) ·
modular monolith with executable architecture rules. Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Run it locally

Requirements: Docker, Node ≥ 22 with pnpm, Python 3, GNU Make (Git Bash on Windows).

```bash
pnpm install
make supabase-start   # Supabase local: Postgres, Auth, Storage
make env              # writes .env and apps/web/.env.local (random dev passwords)
make install          # builds the API dev image
make dev              # migrations + seed; API on :8000, web on :3000
```

Development users (`admin@`, `revisor@`, `pyme.a@`, `pyme.b@`, `mentor@auditor.local`) are
created by `make seed` with the random passwords stored in `.env` (`SEED_*_PASSWORD`); they are
never created in pilot or production. Locally the AI is the deterministic `FakeLLMProvider`; use
only the synthetic PDFs in `apps/web/e2e/fixtures/` (regenerate with `make fixtures`).

To use Groq locally: `LLM_PROVIDER=groq`, `LLM_API_KEY=<key>` in `.env`, then restart the API.

## Quality gates

| Command | What it runs |
|---|---|
| `make check` | ruff, ESLint, Prettier · mypy --strict, tsc · import-linter, dependency-cruiser · OpenAPI client drift + Schemathesis · pytest (coverage ≥ 85 % in domain/application) + Vitest · gitleaks, bandit, pip-audit, pnpm audit |
| `make e2e` | Playwright against the running stack (full flow, roles, axe WCAG 2.1 AA) |
| `make acceptance` | clean database + seed + A/B isolation walker + full E2E |
| `make docker-build` | production images (`auditor-api`, `auditor-web`) |

## Documentation

- [docs/FINAL_REPORT.md](docs/FINAL_REPORT.md) — what was built, evidence, limitations, next steps
- [docs/DEPLOY.md](docs/DEPLOY.md) — Vercel + Render/Railway + Supabase cloud
- [docs/SECURITY.md](docs/SECURITY.md) — controls and how each one is tested
- [docs/PILOT.md](docs/PILOT.md) — running the pilot, consent and retention
- [docs/RUNBOOK.md](docs/RUNBOOK.md) — operations and incident procedures
- [docs/DECISIONS.md](docs/DECISIONS.md) · [docs/PROGRESS.md](docs/PROGRESS.md) · [docs/BACKLOG.md](docs/BACKLOG.md)
