"""A small synthetic world shared by integration tests: two companies and one user per role."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from auditor.shared.domain.actor import Role
from tests.support.auth import auth_headers
from tests.support.factories import create_company, create_user


@dataclass(frozen=True)
class Member:
    id: UUID
    headers: dict[str, str]


@dataclass(frozen=True)
class World:
    company_a: UUID
    company_b: UUID
    admin: Member
    reviewer: Member
    other_reviewer: Member
    sme_a: Member
    sme_b: Member
    mentor: Member


async def build_world(session: AsyncSession) -> World:
    company_a = await create_company(session, "Empresa sintética A")
    company_b = await create_company(session, "Empresa sintética B")

    async def member(role: Role, company: UUID | None = None) -> Member:
        user = await create_user(session, role, company)
        return Member(id=user.id, headers=auth_headers(user.id))

    return World(
        company_a=company_a,
        company_b=company_b,
        admin=await member(Role.ADMIN),
        reviewer=await member(Role.REVIEWER),
        other_reviewer=await member(Role.REVIEWER),
        sme_a=await member(Role.SME, company_a),
        sme_b=await member(Role.SME, company_b),
        mentor=await member(Role.MENTOR),
    )
