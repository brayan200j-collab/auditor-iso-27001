from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from auditor.identity.domain.user import User
from auditor.shared.domain.actor import Role
from auditor.shared.domain.pagination import Page, PageRequest


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


@dataclass(frozen=True, slots=True)
class NewUser:
    id: UUID
    email: str
    full_name: str
    role: Role
    company_id: UUID | None


@dataclass(frozen=True, slots=True)
class UserFilters:
    role: Role | None = None
    company_id: UUID | None = None
    search: str | None = None


class UserRepository(Protocol):
    async def get(self, user_id: UUID) -> User | None: ...

    async def get_by_email(self, email: str) -> User | None: ...

    async def list(self, filters: UserFilters, page: PageRequest) -> Page[User]: ...

    async def add(self, user: NewUser) -> User: ...

    async def update(
        self,
        user_id: UUID,
        *,
        full_name: str | None = None,
        active: bool | None = None,
        company_id: UUID | None = None,
    ) -> User: ...


class CompanyDirectory(Protocol):
    """Read access to company names, provided by the companies module."""

    async def name_of(self, company_id: UUID) -> str | None: ...

    async def exists(self, company_id: UUID) -> bool: ...
