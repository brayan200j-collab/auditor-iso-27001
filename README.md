# Auditor Virtual

> **Auditor Virtual ISO/IEC 27001 con IA es una aplicación web de autoevaluación inicial que analiza documentación empresarial mediante inteligencia artificial y la contrasta con un checklist propio alineado con ISO/IEC 27001:2022, utilizando CIS Controls v8.1 y NIST CSF 2.0 como referencias complementarias. Los resultados generados por la IA son revisados y validados por una persona antes de ser presentados a la empresa.**

Este resultado corresponde a una autoevaluación inicial y no constituye una certificación ISO/IEC 27001 ni reemplaza una auditoría realizada por un organismo acreditado.

Academic project (Electiva Emprendimiento en TIC, Universidad Santiago de Cali) for SMEs in Valle del Cauca.

## Quick start (local)

Requirements: Docker, Node ≥ 22, pnpm, Python 3 (for `scripts/dev_env.py`), GNU Make, Git Bash on Windows.

```bash
pnpm install
make supabase-start   # Supabase local: Postgres, Auth, Storage
make env              # writes .env and apps/web/.env.local (random dev passwords)
make install          # builds the API dev image
make dev              # API on :8000, web on :3000
```

Quality gates: `make check`. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md),
[docs/DECISIONS.md](docs/DECISIONS.md) and [docs/PROGRESS.md](docs/PROGRESS.md).
