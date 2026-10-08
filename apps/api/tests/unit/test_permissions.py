"""The matrix must match CLAUDE.md section 7 exactly; this test transcribes that table literally."""

from __future__ import annotations

from uuid import uuid4

import pytest

from auditor.identity.domain.permissions import (
    PERMISSION_MATRIX,
    Permission,
    ResourceOwnership,
    Scope,
    authorize,
    can_access,
)
from auditor.shared.domain.actor import Actor, Role
from auditor.shared.domain.errors import ForbiddenError

A, R, S, M = Role.ADMIN, Role.REVIEWER, Role.SME, Role.MENTOR
ALL, ASSIGNED, OWN = Scope.ALL, Scope.ASSIGNED, Scope.OWN_COMPANY

EXPECTED: dict[Permission, dict[Role, Scope]] = {
    Permission.MANAGE_COMPANIES: {A: ALL},
    Permission.MANAGE_USERS: {A: ALL},
    Permission.MANAGE_CHECKLIST: {A: ALL},
    Permission.MANAGE_RETENTION: {A: ALL},
    Permission.ASSIGN_REVIEWER: {A: ALL},
    Permission.VIEW_EVALUATIONS: {A: ALL, R: ASSIGNED, S: OWN},
    Permission.CREATE_EVALUATION: {S: OWN},
    Permission.UPLOAD_DOCUMENTS: {S: OWN},
    Permission.VIEW_AI_FINDINGS: {A: ALL, R: ASSIGNED},
    Permission.REVIEW_FINDINGS: {A: ALL, R: ASSIGNED},
    Permission.DECIDE_EVALUATION: {A: ALL, R: ASSIGNED},
    Permission.GENERATE_REPORT: {A: ALL, R: ASSIGNED},
    Permission.RETRY_PROCESSING: {A: ALL, R: ASSIGNED},
    Permission.VIEW_APPROVED_RESULTS: {A: ALL, R: ASSIGNED, S: OWN},
    Permission.DOWNLOAD_REPORT: {A: ALL, R: ASSIGNED, S: OWN},
    Permission.SUBMIT_FEEDBACK: {S: OWN},
    Permission.VIEW_AUDIT_LOGS: {A: ALL},
    Permission.VIEW_METRICS: {A: ALL},
    Permission.VIEW_ANONYMIZED_METRICS: {A: ALL, M: ALL},
}


def test_every_permission_is_specified() -> None:
    assert set(EXPECTED) == set(Permission)


@pytest.mark.parametrize("role", list(Role))
@pytest.mark.parametrize("permission", list(Permission))
def test_matrix_matches_specification(role: Role, permission: Permission) -> None:
    expected = EXPECTED[permission].get(role)
    actor = Actor(user_id=uuid4(), role=role, company_id=uuid4())
    assert PERMISSION_MATRIX[role].get(permission) == expected
    if expected is None:
        with pytest.raises(ForbiddenError):
            authorize(actor, permission)
    else:
        assert authorize(actor, permission) is expected


def test_sme_never_sees_unapproved_ai_findings() -> None:
    sme = Actor(user_id=uuid4(), role=Role.SME, company_id=uuid4())
    with pytest.raises(ForbiddenError):
        authorize(sme, Permission.VIEW_AI_FINDINGS)


def test_scopes_are_checked_against_resource_ownership() -> None:
    company, other_company = uuid4(), uuid4()
    reviewer = Actor(user_id=uuid4(), role=Role.REVIEWER)
    sme = Actor(user_id=uuid4(), role=Role.SME, company_id=company)
    admin = Actor(user_id=uuid4(), role=Role.ADMIN)
    mentor = Actor(user_id=uuid4(), role=Role.MENTOR)
    assigned = ResourceOwnership(company_id=other_company, reviewer_id=reviewer.user_id)
    unassigned = ResourceOwnership(company_id=company, reviewer_id=None)

    view = Permission.VIEW_EVALUATIONS
    assert can_access(admin, view, unassigned)
    assert can_access(reviewer, view, assigned)
    assert not can_access(reviewer, view, unassigned)
    assert can_access(sme, view, unassigned)
    assert not can_access(sme, view, assigned)
    assert not can_access(mentor, view, unassigned)
    orphan_sme = Actor(user_id=uuid4(), role=Role.SME, company_id=None)
    assert not can_access(orphan_sme, view, unassigned)
