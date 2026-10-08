from __future__ import annotations

from auditor.identity.application.ports import UserFilters, UserRepository
from auditor.identity.domain.permissions import Permission, authorize
from auditor.identity.domain.user import User
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.pagination import Page, PageRequest


class ListUsers:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def execute(self, actor: Actor, filters: UserFilters, page: PageRequest) -> Page[User]:
        authorize(actor, Permission.MANAGE_USERS)
        return await self._users.list(filters, page)
