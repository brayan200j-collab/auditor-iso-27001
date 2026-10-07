from __future__ import annotations

from auditor.companies.application.ports import CompanyRepository
from auditor.companies.domain.company import Company
from auditor.identity.public import Permission, authorize
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.pagination import Page, PageRequest


class ListCompanies:
    def __init__(self, companies: CompanyRepository) -> None:
        self._companies = companies

    async def execute(self, actor: Actor, search: str | None, page: PageRequest) -> Page[Company]:
        authorize(actor, Permission.MANAGE_COMPANIES)
        return await self._companies.list(search, page)
