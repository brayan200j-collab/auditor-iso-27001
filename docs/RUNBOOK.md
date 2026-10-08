# Runbook

Operational procedures for the pilot. Every procedure that touches data is recorded in
`audit_logs` or in the team's incident log. Never copy document content into tickets or chats.

## 1. Health and logs
- `GET /healthz` (process alive) and `GET /readyz` (database reachable).
- Logs are JSON with `request_id`; the same id is returned to the user in error messages
  (`{code, message, request_id}`), so a support request can be traced without sharing data.
- Logs never contain document text, tokens or passwords.

## 2. Users and companies
- **First admin:** invite the user in Supabase Auth, then insert the row in `public.users` with
  role `ADMIN` and `company_id = NULL` (one-off SQL, recorded in the incident log). Afterwards all
  users and companies are managed from the admin screens.
- **Deactivate a user:** Usuarios → Desactivar (sessions stop working on the next request).
- **Reviewer assignment:** Evaluaciones (admin) → choose the reviewer → Asignar.

## 3. Processing problems
| Symptom | Cause | Action |
|---|---|---|
| Evaluation in **Error** with "interrumpido, reintentar" | the API restarted mid-job | Reviewer/admin presses **Reintentar**; it resumes from the first criterion without a finding |
| Error "límite de uso" (`QUOTA_EXCEEDED`) | quota per evaluation/company or provider daily limit | wait (Groq free tier resets daily) or raise `MAX_*` deliberately; retry |
| Many `llm_rate_limited` logs | provider 429 | lower `LLM_MAX_CONCURRENCY`; the client already honours `Retry-After` |
| Report state **FAILED** | rendering/storage error | results page → **Generar informe** (reviewer/admin); check logs by `request_id` |
| Jobs stuck in `RUNNING` | instance killed | the sweeper requeues them after `JOB_RUNNING_TIMEOUT_SECONDS`; restart the API if needed |
| 429 `RATE_LIMITED` for a user | per-session limit | wait for `Retry-After`; adjust `RATE_LIMIT_*` only with evidence |

Run a single API instance: the job runner, retention sweep and rate limits are in-process.

## 4. Retention and deletion requests
- Automatic: PDFs and fragments are purged `RETENTION_DAYS` after approval; check
  `RETENTION_PURGED` entries in the audit log.
- On demand: as admin, `POST /api/v1/retention/purge` (only expired documents).
- **Earlier deletion requested by a company or data subject (Ley 1581 de 2012):**
  1. Record the request (who, what, when) and verify identity with the company contact.
  2. Before the analysis starts, the SME can delete documents from the evaluation page (audited).
  3. Otherwise, run in a transaction, replacing `<evaluation_id>`:
     ```sql
     -- documents and fragments of one evaluation (Storage objects deleted from the dashboard)
     DELETE FROM document_chunks WHERE document_id IN
       (SELECT id FROM documents WHERE evaluation_id = '<evaluation_id>');
     UPDATE documents SET status = 'PURGED', storage_path = NULL, purged_at = now()
       WHERE evaluation_id = '<evaluation_id>';
     ```
     Delete the objects under `companies/<company_id>/evaluations/<evaluation_id>/` in both
     buckets, then insert an audit entry (`RETENTION_PURGED`, details `{"reason": "request"}`).
  4. Confirm to the requester within the legal deadline.

## 5. Secrets rotation
- Groq key: create a new key, update `LLM_API_KEY`, redeploy, revoke the old key.
- Supabase service role key or database password: rotate in Supabase, update the API variables,
  redeploy. The web app holds no private keys.
- After any suspected leak: rotate, review `ACCESS_DENIED` and `REPORT_DOWNLOADED` audit entries.

## 6. Backups and restore
Supabase cloud provides daily backups on paid plans only; on the free tier export the database
weekly during the pilot (`pg_dump` with the session pooler) to encrypted storage owned by the
team. Restoring: create a new project, restore the dump, run `alembic upgrade head`, recreate the
buckets; Storage objects are not part of the dump.

## 7. Releasing a new version
1. `make check` and `make acceptance` green on the branch; CI green (including Trivy).
2. Database migrations are additive and reversible; the API runs `alembic upgrade head` before
   starting.
3. Changing the consent text or the retention period requires a new consent version
   (`CURRENT_CONSENT_VERSION`).
4. Changing the checklist: create a draft version from Checklist, edit, publish. Evaluations keep
   the version they were analysed with.
