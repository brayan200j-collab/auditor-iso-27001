# Deployment guide

Target (CLAUDE.md section 4): **Vercel** (web) + **Render or Railway** (API, Docker) + **Supabase
cloud** (Postgres, Auth, Storage). The MVP is ready to deploy but has **not** been deployed; every
step below must be verified by the team in the real accounts.

```
Browser ──HTTPS──► Vercel (Next.js) ──HTTPS + user JWT──► Render/Railway (FastAPI container)
                                                              │
                         Supabase cloud: Postgres · Auth · Storage (private) ◄──┘
                         Groq API (only provider allowed with real data)
```

## 1. Supabase cloud
1. Create a project (region close to Colombia, e.g. `sa-east-1`). Note the project URL, the
   **publishable** key, the **service role** key (secret) and the Postgres connection string
   (use the session pooler, port 5432, with `sslmode=require`).
2. **Auth:** disable public sign-ups (users are invited by an admin); set the Site URL to the web
   URL and add `https://<web>/auth/confirm` to the redirect URLs; copy the email templates from
   `supabase/templates/` (invite and recovery use `token_hash`). Configure a real SMTP sender.
3. **Storage:** create the private buckets `documents` and `reports` (no public access, 20 MiB,
   `application/pdf`), as in `supabase/config.toml`. Add no policies: only the API (service role)
   reaches them and downloads use signed URLs.
4. **Database:** run the migrations from the API image (they enable RLS deny-by-default):
   ```bash
   docker run --rm -e DATABASE_URL=... -e APP_ENV=production ... auditor-api:latest alembic upgrade head
   docker run --rm ... auditor-api:latest python -m auditor.seed checklist
   ```
   The seed refuses to create development users outside `local`/`test`. Create the first admin
   by inviting the user in Supabase Auth and inserting its row with role `ADMIN` (RUNBOOK §2).

## 2. API (Render or Railway)
- Build: `apps/api/Dockerfile`, target `runtime`, context = repository root
  (`docker build -f apps/api/Dockerfile --target runtime .`). Runs as a non-root user, exposes
  8000, health check `/healthz`, readiness `/readyz`.
- Run **one instance** (the job runner, retention sweep and rate limits are in-process; D-028,
  D-038, D-040). Pre-deploy command: `alembic upgrade head`.
- Environment variables (secrets marked 🔒; never sent to the browser):

| Variable | Value |
|---|---|
| `APP_ENV` | `pilot` or `production` |
| `DATABASE_URL` 🔒 | `postgresql+psycopg://...` (Supabase pooler, `sslmode=require`) |
| `SUPABASE_URL` / `SUPABASE_PUBLIC_URL` | project URL (public URL is used in signed links) |
| `SUPABASE_JWT_ISSUER` | `https://<project>.supabase.co/auth/v1` |
| `SUPABASE_JWT_AUDIENCE` | `authenticated` |
| `SUPABASE_SERVICE_ROLE_KEY` 🔒 | service role key |
| `ALLOWED_ORIGINS` | the web origin only, e.g. `https://auditor-virtual.vercel.app` |
| `LLM_PROVIDER` | `groq` (startup fails with any provider not allowed for real data) |
| `LLM_API_KEY` 🔒 | Groq key |
| `LLM_MODEL` | `openai/gpt-oss-120b` (confirm availability) |
| `LLM_PROVIDERS_ALLOWED_FOR_REAL_DATA` | `groq` |
| `LLM_MAX_CONCURRENCY`, `MAX_TOKENS_PER_CALL`, `MAX_LLM_CALLS_PER_EVALUATION`, `MAX_EVALUATIONS_PER_COMPANY` | free-tier friendly defaults: 2, 2000, 80, 10 |
| `EVIDENCE_TOP_K` | 5 |
| `RETENTION_DAYS` / `RETENTION_SWEEP_INTERVAL_SECONDS` | 90 / 21600 (changing the days requires a new consent version) |
| `SIGNED_URL_TTL_SECONDS` | 120 |
| `RATE_LIMIT_DEFAULT`, `RATE_LIMIT_UPLOAD`, `RATE_LIMIT_START`, `RATE_LIMIT_DOWNLOAD` | 300/minute, 20/hour, 20/hour, 60/hour |
| `SENTRY_DSN` 🔒 | optional |

`auth_provider`/`storage_provider` default to `supabase`; the test adapters refuse to start
outside `local`/`test`.

## 3. Web (Vercel)
- Root directory `apps/web`, framework Next.js, install `pnpm install --frozen-lockfile`
  (Vercel detects the pnpm workspace), build `pnpm build`.
- Environment variables (all public by design; set them for **build and runtime**, Next.js
  inlines `NEXT_PUBLIC_*` at build time):
  `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`, `NEXT_PUBLIC_API_URL`
  (the API URL), `NEXT_PUBLIC_SITE_URL` (the web URL). Optional: `AUTH_RATE_LIMIT_PER_IP`,
  `AUTH_RATE_LIMIT_PER_EMAIL`.
- Alternative to Vercel: the production image `apps/web/Dockerfile` (standalone output, non-root,
  per-request CSP nonce) built with `--build-arg NEXT_PUBLIC_...` (see `make docker-build`).

## 4. After deploying (smoke test)
1. `GET https://<api>/readyz` → 200; `https://<web>/login` has a `content-security-policy` header
   with a nonce and HSTS.
2. Log in as the admin, create a company, invite an SME user (email arrives, password is set).
3. With a **synthetic** PDF (`apps/web/e2e/fixtures/politica_seguridad_sintetica.pdf`): upload,
   start the analysis, review as the reviewer, approve, download the report as the SME.
4. Check `Registro de auditoría` shows the actions and `Métricas` shows real counts.
5. From another company's user, open the first company's evaluation URL → generic "not found".

## 5. Images and CI
`make docker-build` builds `auditor-api:latest` and `auditor-web:latest`; CI scans both with Trivy
(HIGH/CRITICAL fail) and runs `make check` and `make acceptance` on every push.
