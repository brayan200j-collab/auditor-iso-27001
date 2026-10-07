"""In-memory test doubles for external services (never used by production code)."""

from __future__ import annotations

from uuid import UUID, uuid4

from auditor.shared.domain.errors import ConflictError


class FakeAuthAdmin:
    def __init__(self) -> None:
        self.accounts: dict[str, UUID] = {}
        self.invited: list[str] = []
        self.banned: set[UUID] = set()
        self.deleted: list[UUID] = []

    async def find_user_id(self, email: str) -> UUID | None:
        return self.accounts.get(email.lower())

    async def create_user(self, email: str, password: str) -> UUID:
        return self._register(email)

    async def invite_user(self, email: str, redirect_to: str | None) -> UUID:
        self.invited.append(email.lower())
        return self._register(email)

    async def set_banned(self, user_id: UUID, banned: bool) -> None:
        if banned:
            self.banned.add(user_id)
        else:
            self.banned.discard(user_id)

    async def delete_user(self, user_id: UUID) -> None:
        self.deleted.append(user_id)
        self.accounts = {email: uid for email, uid in self.accounts.items() if uid != user_id}

    def _register(self, email: str) -> UUID:
        key = email.lower()
        if key in self.accounts:
            raise ConflictError("Ya existe una cuenta con ese correo.")
        self.accounts[key] = uuid4()
        return self.accounts[key]
