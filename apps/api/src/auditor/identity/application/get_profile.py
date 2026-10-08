from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from auditor.identity.application.ports import CompanyDirectory, UserRepository
from auditor.shared.domain.actor import Actor, Role
from auditor.shared.domain.errors import UnauthorizedError


@dataclass(frozen=True, slots=True)
class Profile:
    id: UUID
    email: str
    full_name: str
    role: Role
    company_id: UUID | None
    company_name: str | None


class GetProfile:
    def __init__(self, users: UserRepository, companies: CompanyDirectory) -> None:
        self._users = users
        self._companies = companies

    async def execute(self, actor: Actor) -> Profile:
        user = await self._users.get(actor.user_id)
        if user is None:
            raise UnauthorizedError()
        company_name = await self._companies.name_of(user.company_id) if user.company_id else None
        return Profile(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            company_id=user.company_id,
            company_name=company_name,
        )
