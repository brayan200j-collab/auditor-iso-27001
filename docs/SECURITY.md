# Security

Controls implemented in the MVP, guided by OWASP ASVS (CLAUDE.md sections 8, 9 and 9.1), and how
each one is verified. Report vulnerabilities privately to the project team; never open a public
issue with exploit details.

## Authentication and sessions
| Control | Implementation | Verified by |
|---|---|---|
| JWT verification | Supabase JWKS (ES256) with cache: signature, expiry, audience, issuer | `tests/integration/test_supabase_auth.py`, `tests/unit/test_token_verifier.py` |
| Role and company from the database, never from the client | `ResolveActor` loads the user row | permission matrix tests |
| Session cookies | HttpOnly, `Secure` in production, `SameSite=Lax`; Supabase runs only on the server | `src/lib/auth/supabase.ts`, `src/proxy.ts` |
| Login and recovery throttling | per-IP and per-email fixed windows in the Next.js server; responses never reveal whether an email exists | `src/lib/rate-limit.test.ts`, `LoginForm.test.tsx` |
| No demo credentials | dev users come from `make seed` (env vars), refused in pilot/production | `tests/unit/test_seed.py`, frontend tests |

## Authorization and multi-tenancy
| Control | Implementation | Verified by |
|---|---|---|
| Single permission matrix | `identity/domain/permissions.py` (ALL / ASSIGNED / OWN_COMPANY) | `tests/unit/test_permissions.py` walks every role × permission |
| Company-scoped repositories and generic 404 | `EvaluationAccess.require`; denied attempts audited as `ACCESS_DENIED` | integration tests per module |
| Authentication on every endpoint | OpenAPI walker calls every route without a token | `tests/integration/test_authentication_required.py` |
| Isolation A vs B on every endpoint | OpenAPI walker swapping UUIDs between companies | added in S18 (see PROGRESS.md) |
| RLS deny-by-default | all tables, `anon`/`authenticated` have no grants | `tests/integration/test_schema.py` |
| SME never sees unapproved AI output | separate layers `ai_findings` → `human_reviews` → `final_findings`; results only after approval | `test_review_api.py`, `test_results_api.py` |

## Input, files and output
| Control | Implementation | Verified by |
|---|---|---|
| PDF validation | extension, MIME, `%PDF-` signature, ≤ 20 MB streamed cut-off, ≤ 30 pages counted before extraction, encrypted/corrupt/scanned rejected, JavaScript and attachments rejected, sanitized names | `tests/integration/test_documents_api.py` |
| Private storage | system-generated paths, never sent to the browser; downloads via signed URL (`SIGNED_URL_TTL_SECONDS`) after authorization, audited | `test_reports_api.py` |
| Strict request models | unknown query parameters, control characters and NUL bytes rejected; LIKE wildcards escaped | `tests/integration/test_contract.py` (Schemathesis) |
| No raw HTML | React escapes; no `dangerouslySetInnerHTML`; report template autoescaped and WeasyPrint refuses external URLs | `tests/unit/test_report_renderer_safety.py` |
| Errors | `{code, message, request_id}` in Spanish, no stack traces | error handler tests |

## Headers and transport
- **Web:** per-request nonce CSP (`script-src 'self' 'nonce-…' 'strict-dynamic'`, `connect-src 'self'`, `frame-ancestors 'none'`, `object-src 'none'`, `form-action 'self'`, `base-uri 'self'`, `upgrade-insecure-requests` in production), `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, COOP, HSTS in production. Verified by `src/lib/csp.test.ts` and `e2e/a11y.spec.ts`.
- **API:** restrictive CSP, `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store`, HSTS outside local; explicit CORS allow-list (`ALLOWED_ORIGINS`).

## Rate limiting (API)
Per session (hash of the bearer token; the web server is the only client IP), in memory:
`RATE_LIMIT_DEFAULT` (300/min) on every API route, `RATE_LIMIT_UPLOAD` (20/h), `RATE_LIMIT_START`
(20/h, also retry) and `RATE_LIMIT_DOWNLOAD` (60/h). Exceeding a limit returns 429 `RATE_LIMITED`
with `Retry-After`. Verified by `tests/integration/test_rate_limits.py`. A multi-instance
deployment needs a shared store (Redis is out of scope for the MVP; see D-040).

## AI-specific controls
- Documents are untrusted data: the system prompt forbids following instructions inside them,
  fragments are delimited and delimiter look-alikes neutralized, the model has no tools or
  internet, output is validated against a strict JSON Schema plus Pydantic (`test_ai_engine.py`,
  prompt-injection PDF).
- Citations are verified against the real fragment; unverified quotes are flagged and never reach
  the company.
- Minimal data to the provider: 3–5 fragments, documents named "Documento N", no company or user
  data; `llm_calls` stores no document text.
- Quotas (`QUOTA_EXCEEDED`), bounded concurrency, `Retry-After`/backoff on 429, resumable runs.
- Providers allowed with real data are restricted by `LLM_PROVIDERS_ALLOWED_FOR_REAL_DATA`;
  `fake` and `gemini` never start in pilot/production.

## Privacy and retention
Versioned consent before upload; PDFs and fragments deleted `RETENTION_DAYS` after approval
(audited `RETENTION_PURGED`); logs never contain document content, tokens or passwords. See
`docs/PILOT.md`.

## Supply chain and secrets
`make check` and CI run gitleaks, bandit, pip-audit and `pnpm audit` (high/critical fail). Secrets
only in environment variables; `.env` is git-ignored and generated locally. Images are scanned
with Trivy in CI. Dependabot keeps dependencies updated.

## Known limitations
- In-memory rate limits and job runner are per instance (single API instance for the pilot).
- No antivirus: `FileScanner` is an extension point (no-op).
- The real Groq and Gemini APIs, the provider's privacy terms and the legal texts have not been
  verified in this environment (see `FINAL_REPORT.md`).
