"""audit action DOCUMENT_VIEWED

Reviewers (and the owning company) can open the original PDF of an evaluation; every opening is
audited, so the action vocabulary of `audit_logs` gains DOCUMENT_VIEWED.

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-08 15:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_BEFORE = (
    "LOGIN",
    "LOGOUT",
    "ACCESS_DENIED",
    "COMPANY_CREATED",
    "COMPANY_UPDATED",
    "USER_CREATED",
    "USER_UPDATED",
    "REVIEWER_ASSIGNED",
    "EVALUATION_CREATED",
    "CONSENT_GIVEN",
    "DOCUMENT_UPLOADED",
    "DOCUMENT_REJECTED",
    "DOCUMENT_DELETED",
    "PROCESSING_STARTED",
    "PROCESSING_FINISHED",
    "PROCESSING_FAILED",
    "PROCESSING_RETRIED",
    "FINDINGS_GENERATED",
    "FINDING_REVIEWED",
    "EVALUATION_APPROVED",
    "EVALUATION_REJECTED",
    "REPORT_GENERATED",
    "REPORT_DOWNLOADED",
    "CHECKLIST_VERSION_CREATED",
    "CHECKLIST_VERSION_PUBLISHED",
    "FEEDBACK_SUBMITTED",
    "RETENTION_PURGED",
    "QUOTA_EXCEEDED",
)


def _check(actions: tuple[str, ...]) -> str:
    quoted = ", ".join(f"'{action}'" for action in actions)
    return f"action IN ({quoted})"


def upgrade() -> None:
    op.execute("ALTER TABLE audit_logs DROP CONSTRAINT ck_audit_logs_action_valid")
    op.execute(
        "ALTER TABLE audit_logs ADD CONSTRAINT ck_audit_logs_action_valid "
        f"CHECK ({_check((*_BEFORE, 'DOCUMENT_VIEWED'))})"
    )


def downgrade() -> None:
    # audit_logs is append-only: entries already written are kept, so the old rule is restored
    # without validating existing rows.
    op.execute("ALTER TABLE audit_logs DROP CONSTRAINT ck_audit_logs_action_valid")
    op.execute(
        "ALTER TABLE audit_logs ADD CONSTRAINT ck_audit_logs_action_valid "
        f"CHECK ({_check(_BEFORE)}) NOT VALID"
    )
