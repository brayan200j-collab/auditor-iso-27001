from __future__ import annotations

from auditor.companies.application.inputs import CompanyInput, clean_company_input
from auditor.companies.application.ports import CompanyRepository
from auditor.companies.domain.company import Company
from auditor.identity.public import Permission, authorize
from auditor.shared.application.ports import AuditLogger, UnitOfWork
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.audit import AuditAction, AuditEntry
from auditor.shared.domain.errors import ConflictError


class CreateCompany:
    def __init__(self, companies: CompanyRepository, audit: AuditLogger, uow: UnitOfWork) -> None:
        self._companies = companies
        self._audit = audit
        self._uow = uow

    async def execute(self, actor: Actor, data: CompanyInput) -> Company:
        authorize(actor, Permission.MANAGE_COMPANIES)
        clean = clean_company_input(data)
        if clean.tax_id and await self._companies.get_by_tax_id(clean.tax_id):
            raise ConflictError("Ya existe una empresa con ese NIT.")
        company = await self._companies.add(clean)
        await self._audit.record(
            AuditEntry(
                action=AuditAction.COMPANY_CREATED,
                actor_id=actor.user_id,
                actor_role=actor.role,
                company_id=company.id,
                resource_type="company",
                resource_id=company.id,
            )
        )
        await self._uow.commit()
        return company
