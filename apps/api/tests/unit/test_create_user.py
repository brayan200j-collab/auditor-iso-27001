"""Compensation: an invited identity is removed when the profile cannot be stored."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from auditor.identity.application.create_user import CreateUser, CreateUserInput
from auditor.identity.application.ports import NewUser, UserFilters
from auditor.identity.domain.user import User
from auditor.shared.domain.actor import Actor, Role
from auditor.shared.domain.audit import AuditEntry
from auditor.shared.domain.pagination import Page, PageRequest
from tests.support.fakes import FakeAuthAdmin


class FailingUsers:
    async def get(self, user_id: UUID) -> User | None:
        return None

    async def get_by_email(self, email: str) -> User | None:
        return None

    async def list(self, filters: UserFilters, page: PageRequest) -> Page[User]:
        return Page(items=[], total=0, page=1, page_size=20)

    async def add(self, user: NewUser) -> User:
        raise RuntimeError("database unavailable")

    async def update(self, user_id: UUID, **_: object) -> User:
        raise NotImplementedError


class Directory:
    async def name_of(self, company_id: UUID) -> str | None:
        return "Empresa"

    async def exists(self, company_id: UUID) -> bool:
        return True


class NullAudit:
    async def record(self, entry: AuditEntry) -> None:
        return None

    async def record_immediately(self, entry: AuditEntry) -> None:
        return None


class RecordingUow:
    def __init__(self) -> None:
        self.rolled_back = False

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        self.rolled_back = True


async def test_invited_account_is_deleted_when_profile_creation_fails() -> None:
    auth_admin = FakeAuthAdmin()
    uow = RecordingUow()
    use_case = CreateUser(FailingUsers(), auth_admin, Directory(), NullAudit(), uow)
    admin = Actor(user_id=uuid4(), role=Role.ADMIN)

    with pytest.raises(RuntimeError):
        await use_case.execute(
            admin,
            CreateUserInput(
                email="nueva@example.test", full_name="Nueva", role=Role.MENTOR, company_id=None
            ),
        )

    assert uow.rolled_back
    assert len(auth_admin.deleted) == 1
    assert auth_admin.accounts == {}


def test_user_entity_converts_to_actor() -> None:
    user = User(
        id=uuid4(),
        email="a@example.test",
        full_name="A",
        role=Role.SME,
        active=True,
        company_id=uuid4(),
        created_at=datetime.now(UTC),
    )
    actor = user.as_actor()
    assert (actor.user_id, actor.role, actor.company_id) == (user.id, user.role, user.company_id)
