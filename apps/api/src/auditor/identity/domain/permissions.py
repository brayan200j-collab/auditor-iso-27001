"""The permission matrix (CLAUDE.md section 7). The single source of truth for authorization.

Each role maps permissions to a *scope*. Use cases first call `authorize()` and then apply the scope
to the concrete resource with `can_access()`: company and evaluation ownership are always checked
against data loaded from the database.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from uuid import UUID

from auditor.shared.domain.actor import Actor, Role
from auditor.shared.domain.errors import ForbiddenError


class Permission(StrEnum):
    MANAGE_COMPANIES = "MANAGE_COMPANIES"
    MANAGE_USERS = "MANAGE_USERS"
    MANAGE_CHECKLIST = "MANAGE_CHECKLIST"
    ASSIGN_REVIEWER = "ASSIGN_REVIEWER"
    VIEW_EVALUATIONS = "VIEW_EVALUATIONS"
    CREATE_EVALUATION = "CREATE_EVALUATION"
    UPLOAD_DOCUMENTS = "UPLOAD_DOCUMENTS"
    VIEW_AI_FINDINGS = "VIEW_AI_FINDINGS"
    REVIEW_FINDINGS = "REVIEW_FINDINGS"
    DECIDE_EVALUATION = "DECIDE_EVALUATION"
    GENERATE_REPORT = "GENERATE_REPORT"
    RETRY_PROCESSING = "RETRY_PROCESSING"
    VIEW_APPROVED_RESULTS = "VIEW_APPROVED_RESULTS"
    DOWNLOAD_REPORT = "DOWNLOAD_REPORT"
    SUBMIT_FEEDBACK = "SUBMIT_FEEDBACK"
    VIEW_AUDIT_LOGS = "VIEW_AUDIT_LOGS"
    VIEW_METRICS = "VIEW_METRICS"
    VIEW_ANONYMIZED_METRICS = "VIEW_ANONYMIZED_METRICS"


class Scope(StrEnum):
    ALL = "ALL"
    ASSIGNED = "ASSIGNED"
    OWN_COMPANY = "OWN_COMPANY"


_ALL, _ASSIGNED, _OWN = Scope.ALL, Scope.ASSIGNED, Scope.OWN_COMPANY

PERMISSION_MATRIX: MappingProxyType[Role, MappingProxyType[Permission, Scope]] = MappingProxyType(
    {
        Role.ADMIN: MappingProxyType(
            {
                Permission.MANAGE_COMPANIES: _ALL,
                Permission.MANAGE_USERS: _ALL,
                Permission.MANAGE_CHECKLIST: _ALL,
                Permission.ASSIGN_REVIEWER: _ALL,
                Permission.VIEW_EVALUATIONS: _ALL,
                Permission.VIEW_AI_FINDINGS: _ALL,
                Permission.REVIEW_FINDINGS: _ALL,
                Permission.DECIDE_EVALUATION: _ALL,
                Permission.GENERATE_REPORT: _ALL,
                Permission.RETRY_PROCESSING: _ALL,
                Permission.VIEW_APPROVED_RESULTS: _ALL,
                Permission.DOWNLOAD_REPORT: _ALL,
                Permission.VIEW_AUDIT_LOGS: _ALL,
                Permission.VIEW_METRICS: _ALL,
                Permission.VIEW_ANONYMIZED_METRICS: _ALL,
            }
        ),
        Role.REVIEWER: MappingProxyType(
            {
                Permission.VIEW_EVALUATIONS: _ASSIGNED,
                Permission.VIEW_AI_FINDINGS: _ASSIGNED,
                Permission.REVIEW_FINDINGS: _ASSIGNED,
                Permission.DECIDE_EVALUATION: _ASSIGNED,
                Permission.GENERATE_REPORT: _ASSIGNED,
                Permission.RETRY_PROCESSING: _ASSIGNED,
                Permission.VIEW_APPROVED_RESULTS: _ASSIGNED,
                Permission.DOWNLOAD_REPORT: _ASSIGNED,
            }
        ),
        Role.SME: MappingProxyType(
            {
                Permission.VIEW_EVALUATIONS: _OWN,
                Permission.CREATE_EVALUATION: _OWN,
                Permission.UPLOAD_DOCUMENTS: _OWN,
                Permission.VIEW_APPROVED_RESULTS: _OWN,
                Permission.DOWNLOAD_REPORT: _OWN,
                Permission.SUBMIT_FEEDBACK: _OWN,
            }
        ),
        Role.MENTOR: MappingProxyType({Permission.VIEW_ANONYMIZED_METRICS: _ALL}),
    }
)


@dataclass(frozen=True, slots=True)
class ResourceOwnership:
    """Ownership facts of a company-scoped resource, always loaded from the database."""

    company_id: UUID
    reviewer_id: UUID | None = None


def scope_for(actor: Actor, permission: Permission) -> Scope | None:
    return PERMISSION_MATRIX[actor.role].get(permission)


def authorize(actor: Actor, permission: Permission) -> Scope:
    """Returns the actor's scope for the permission or raises ForbiddenError."""
    scope = scope_for(actor, permission)
    if scope is None:
        raise ForbiddenError(detail=f"{actor.role} lacks {permission}")
    return scope


def can_access(actor: Actor, permission: Permission, resource: ResourceOwnership) -> bool:
    scope = scope_for(actor, permission)
    if scope is Scope.ALL:
        return True
    if scope is Scope.ASSIGNED:
        return resource.reviewer_id is not None and resource.reviewer_id == actor.user_id
    if scope is Scope.OWN_COMPANY:
        return actor.company_id is not None and actor.company_id == resource.company_id
    return False
