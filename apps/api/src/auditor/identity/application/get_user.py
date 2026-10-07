from __future__ import annotations

from uuid import UUID

from auditor.identity.application.ports import UserRepository
from auditor.identity.domain.permissions import Permission, authorize
from auditor.identity.domain.user import User
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.errors import ResourceNotFoundError


class GetUser:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def execute(self, actor: Actor, user_id: UUID) -> User:
        authorize(actor, Permission.MANAGE_USERS)
        user = await self._users.get(user_id)
        if user is None:
            raise ResourceNotFoundError()
        return user
