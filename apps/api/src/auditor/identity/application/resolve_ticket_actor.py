from __future__ import annotations

from uuid import UUID

from auditor.identity.application.ports import UserRepository
from auditor.identity.domain.upload_ticket import verify_ticket
from auditor.shared.application.ports import Clock
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.errors import UnauthorizedError


class ResolveTicketActor:
    """Turns an upload ticket into an Actor; role and company still come from the database."""

    def __init__(self, users: UserRepository, secret: bytes, clock: Clock) -> None:
        self._users = users
        self._secret = secret
        self._clock = clock

    async def execute(self, ticket: str, evaluation_id: UUID) -> Actor:
        user_id = verify_ticket(self._secret, ticket, evaluation_id, self._clock.now())
        user = await self._users.get(user_id)
        if user is None or not user.active:
            raise UnauthorizedError(detail="unknown or inactive user")
        return user.as_actor()
