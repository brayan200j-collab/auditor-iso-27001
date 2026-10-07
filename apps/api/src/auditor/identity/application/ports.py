from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class VerifiedToken:
    subject: UUID
    email: str | None


class TokenVerifier(Protocol):
    async def verify(self, token: str) -> VerifiedToken:
        """Validates signature, expiry, audience and issuer. Raises UnauthorizedError."""
        ...


class AuthAdmin(Protocol):
    """Administrative operations on the identity provider (Supabase Auth)."""

    async def find_user_id(self, email: str) -> UUID | None: ...

    async def create_user(self, email: str, password: str) -> UUID: ...

    async def invite_user(self, email: str, redirect_to: str | None) -> UUID: ...

    async def set_banned(self, user_id: UUID, banned: bool) -> None: ...
