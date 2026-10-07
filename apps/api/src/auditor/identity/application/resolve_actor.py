from __future__ import annotations

from auditor.identity.application.ports import TokenVerifier, UserRepository
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.errors import UnauthorizedError


class ResolveActor:
    """Turns a bearer token into an Actor. Role and company always come from the database."""

    def __init__(self, verifier: TokenVerifier, users: UserRepository) -> None:
        self._verifier = verifier
        self._users = users

    async def execute(self, token: str | None) -> Actor:
        if not token:
            raise UnauthorizedError(detail="missing bearer token")
        verified = await self._verifier.verify(token)
        user = await self._users.get(verified.subject)
        if user is None or not user.active:
            raise UnauthorizedError(detail="unknown or inactive user")
        return user.as_actor()
