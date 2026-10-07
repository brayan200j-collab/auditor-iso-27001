from __future__ import annotations

from uuid import UUID

from auditor.companies.application.ports import CompanyRepository
from auditor.companies.domain.company import Company
from auditor.identity.public import Permission, authorize
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.errors import ResourceNotFoundError


class GetCompany:
    def __init__(self, companies: CompanyRepository) -> None:
        self._companies = companies

    async def execute(self, actor: Actor, company_id: UUID) -> Company:
        authorize(actor, Permission.MANAGE_COMPANIES)
        company = await self._companies.get(company_id)
        if company is None:
            raise ResourceNotFoundError()
        return company
