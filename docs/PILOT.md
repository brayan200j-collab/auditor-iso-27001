# Pilot guide (2–3 SMEs, Valle del Cauca)

Operational guide for running the pilot with real company documents. Development and demos use
**synthetic documents only**; real documents are processed only in this pilot, with consent, in a
protected environment, and deleted according to the retention policy.

> Legal texts (privacy policy, conditions, consent) are drafts referring to Ley 1581 de 2012 and
> are marked "revisar con asesor". They must be reviewed by an advisor before the pilot starts.

## 1. Before the pilot (checklist)

| # | Item | Owner | Done |
|---|---|---|---|
| 1 | Legal review of the privacy policy, conditions and consent text (`evaluations/domain/consent.py`, `/privacidad`) | Team + advisor | ☐ |
| 2 | Review the AI provider's data-processing and privacy terms (Groq) and record the decision in `DECISIONS.md` | Team | ☐ |
| 3 | Confirm the ISO/IEC 27001:2022, CIS Controls v8.1 and NIST CSF 2.0 references marked "referencia por confirmar" and publish a new checklist version | Team | ☐ |
| 4 | Deploy with `APP_ENV=pilot`, `LLM_PROVIDER=groq` (the only provider allowed for real data, `LLM_PROVIDERS_ALLOWED_FOR_REAL_DATA=groq`); the API refuses to start with any other provider | Team | ☐ |
| 5 | Private Storage buckets (`documents`, `reports`), HTTPS, strict `ALLOWED_ORIGINS`, secrets only in environment variables | Team | ☐ |
| 6 | No seed users in pilot/production: create companies and users from the admin screens (invitation by email) | Admin | ☐ |
| 7 | Quotas set for the free tier: `MAX_EVALUATIONS_PER_COMPANY`, `MAX_LLM_CALLS_PER_EVALUATION`, `MAX_TOKENS_PER_CALL`, `LLM_MAX_CONCURRENCY` | Team | ☐ |
| 8 | Assign at least one trained reviewer per company | Admin | ☐ |

## 2. Consent

- Each SME user must accept the versioned consent **before uploading** any document. The
  acceptance stores user, evaluation, version (`2026-10-v1`) and a hash of the exact text shown.
- The consent states: purpose (initial self-assessment only), processing by an external inference
  provider whose terms must be reviewed, the free-tier limits, mandatory human review, that the
  result is not an ISO/IEC 27001 certification, the 90-day deletion of original PDFs and
  fragments, the right to delete a document before the analysis, rights under Ley 1581 de 2012,
  and that the user is authorized by the company to share the documents.
- **Any change to the text, including the retention period, requires a new consent version**
  (`CURRENT_CONSENT_VERSION`), so earlier acceptances stay traceable.

## 3. Pilot flow per company

1. Admin creates the company and invites the SME user; assigns a reviewer to each evaluation.
2. SME creates the evaluation, accepts the consent and uploads PDFs (≤ 30 pages, ≤ 20 MB, with
   selectable text; scanned documents are rejected because the MVP has no OCR).
3. SME starts the analysis. The system extracts text, searches evidence per criterion and asks
   the AI only with 3–5 relevant fragments (never the full PDF, never the company name).
4. The reviewer reviews every finding (approve, edit or discard) and approves or rejects the
   evaluation. The SME never sees unreviewed AI output.
5. SME sees the approved results (coverage as counts, prioritized gaps, initial improvement plan),
   downloads the PDF report and answers the validation survey.

## 4. Retention and deletion

| Data | Kept | How it is deleted |
|---|---|---|
| Original PDFs (Storage) and text fragments (`document_chunks`) | `RETENTION_DAYS` (default 90) after approval | Automatic sweep every `RETENTION_SWEEP_INTERVAL_SECONDS` (default 6 h) and on demand by an admin (`POST /api/v1/retention/purge`); each evaluation is audited as `RETENTION_PURGED` |
| Document metadata (name, pages, hash) | Kept, marked `PURGED`, without storage path | — |
| Final findings, PDF report, survey, audit logs | Kept | Manual procedure on request (see below) |
| Documents before the analysis starts | Until the SME deletes them | SME deletes from the evaluation page (audited `DOCUMENT_DELETED`) |

The SME results page shows the date on which the original PDFs will be deleted.

**Data-subject or company requests** (access, correction, deletion under Ley 1581 de 2012): the
admin records the request, verifies identity, and executes the deletion with an audited database
procedure documented in `RUNBOOK.md`. Answer within the legal deadlines.

## 5. Metrics collected

- Technical: PDFs processed correctly, average analysis time, extraction errors, AI calls,
  approximate tokens, findings modified by the reviewer, unauthorized access attempts.
- Value (survey): estimated manual time vs. time using the system, usefulness, ease of use,
  trust, actionable recommendations, willingness to use and to pay.
- Admins see them under **Métricas**; mentors see the same screen in anonymized mode (aggregates
  only). Without data the screen shows "Sin datos aún"; figures are never estimated.

## 6. Communication rules for the pilot

Use "autoevaluación inicial", "cobertura documental preliminar" and "resultado preliminar sujeto a
revisión". Never say "certificado", "Cumple ISO", "porcentaje de cumplimiento" or "Compliance".
Do not claim that the AI is free or that the provider never stores documents; use the wording in
section 1 of `CLAUDE.md`.

## 7. Closing the pilot

1. Export aggregated metrics (Métricas) for the academic report.
2. Run the retention purge for every approved evaluation, or delete earlier if a company asks.
3. Revoke pilot users and rotate the provider API key.
