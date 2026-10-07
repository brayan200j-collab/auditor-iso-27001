from __future__ import annotations

from uuid import uuid4

import pytest

from auditor.shared.application import ports
from auditor.shared.domain.actor import Actor, Role
from auditor.shared.domain.audit import AuditAction, AuditEntry, AuditOutcome
from auditor.shared.domain.errors import (
    DomainError,
    QuotaExceededError,
    ResourceNotFoundError,
)
from auditor.shared.domain.pagination import Page, PageRequest


def test_page_request_offset() -> None:
    assert PageRequest(page=3, page_size=20).offset == 40


@pytest.mark.parametrize(("page", "size"), [(0, 20), (1, 0), (1, 101)])
def test_page_request_rejects_invalid_values(page: int, size: int) -> None:
    with pytest.raises(ValueError, match="page"):
        PageRequest(page=page, page_size=size)


def test_page_holds_items() -> None:
    page = Page(items=[1, 2], total=12, page=1, page_size=2)
    assert page.total == 12
    assert page.items == [1, 2]


@pytest.mark.parametrize(
    ("role", "admin", "reviewer", "sme"),
    [
        (Role.ADMIN, True, False, False),
        (Role.REVIEWER, False, True, False),
        (Role.SME, False, False, True),
        (Role.MENTOR, False, False, False),
    ],
)
def test_actor_role_helpers(role: Role, admin: bool, reviewer: bool, sme: bool) -> None:
    actor = Actor(user_id=uuid4(), role=role)
    assert (actor.is_admin, actor.is_reviewer, actor.is_sme) == (admin, reviewer, sme)


def test_audit_entry_defaults_to_success_without_details() -> None:
    entry = AuditEntry(action=AuditAction.LOGIN)
    assert entry.outcome is AuditOutcome.SUCCESS
    assert entry.details == {}


def test_domain_errors_carry_code_and_spanish_default_message() -> None:
    error = ResourceNotFoundError(detail="internal")
    assert error.code == "NOT_FOUND"
    assert error.message.startswith("El recurso")
    assert error.detail == "internal"
    custom = QuotaExceededError("Límite alcanzado.")
    assert custom.message == "Límite alcanzado."
    assert isinstance(custom, DomainError)


def test_ports_module_exposes_protocols() -> None:
    assert {"Clock", "UnitOfWork", "AuditLogger", "ObjectStorage"} <= set(vars(ports))
