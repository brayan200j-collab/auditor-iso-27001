"""Audit trail vocabulary shared by every module. Entries never contain document content."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID

AuditValue = str | int | float | bool | None


class AuditAction(StrEnum):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    ACCESS_DENIED = "ACCESS_DENIED"
    COMPANY_CREATED = "COMPANY_CREATED"
    COMPANY_UPDATED = "COMPANY_UPDATED"
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    REVIEWER_ASSIGNED = "REVIEWER_ASSIGNED"
    EVALUATION_CREATED = "EVALUATION_CREATED"
    CONSENT_GIVEN = "CONSENT_GIVEN"
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    DOCUMENT_REJECTED = "DOCUMENT_REJECTED"
    DOCUMENT_DELETED = "DOCUMENT_DELETED"
    DOCUMENT_VIEWED = "DOCUMENT_VIEWED"
    PROCESSING_STARTED = "PROCESSING_STARTED"
    PROCESSING_FINISHED = "PROCESSING_FINISHED"
    PROCESSING_FAILED = "PROCESSING_FAILED"
    PROCESSING_RETRIED = "PROCESSING_RETRIED"
    FINDINGS_GENERATED = "FINDINGS_GENERATED"
    FINDING_REVIEWED = "FINDING_REVIEWED"
    EVALUATION_APPROVED = "EVALUATION_APPROVED"
    EVALUATION_REJECTED = "EVALUATION_REJECTED"
    REPORT_GENERATED = "REPORT_GENERATED"
    REPORT_DOWNLOADED = "REPORT_DOWNLOADED"
    CHECKLIST_VERSION_CREATED = "CHECKLIST_VERSION_CREATED"
    CHECKLIST_VERSION_PUBLISHED = "CHECKLIST_VERSION_PUBLISHED"
    FEEDBACK_SUBMITTED = "FEEDBACK_SUBMITTED"
    RETENTION_PURGED = "RETENTION_PURGED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"


class AuditOutcome(StrEnum):
    SUCCESS = "SUCCESS"
    DENIED = "DENIED"
    FAILURE = "FAILURE"


@dataclass(frozen=True, slots=True)
class AuditEntry:
    action: AuditAction
    outcome: AuditOutcome = AuditOutcome.SUCCESS
    actor_id: UUID | None = None
    actor_role: str | None = None
    company_id: UUID | None = None
    resource_type: str | None = None
    resource_id: UUID | None = None
    details: dict[str, AuditValue] = field(default_factory=dict)
