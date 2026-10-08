from __future__ import annotations

from uuid import UUID

from auditor.companies.application.inputs import CompanyInput, clean_company_input
from auditor.companies.application.ports import CompanyRepository
from auditor.companies.domain.company import Company
from auditor.identity.public import Permission, authorize
from auditor.shared.application.ports import AuditLogger, UnitOfWork
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.audit import AuditAction, AuditEntry
from auditor.shared.domain.errors import ConflictError, ResourceNotFoundError


class UpdateCompany:
    def __init__(self, companies: CompanyRepository, audit: AuditLogger, uow: UnitOfWork) -> None:
        self._companies = companies
        self._audit = audit
        self._uow = uow

    async def execute(
        self, actor: Actor, company_id: UUID, data: CompanyInput, active: bool
    ) -> Company:
        authorize(actor, Permission.MANAGE_COMPANIES)
        if await self._companies.get(company_id) is None:
            raise ResourceNotFoundError()
        clean = clean_company_input(data)
        if clean.tax_id:
            other = await self._companies.get_by_tax_id(clean.tax_id)
            if other and other.id != company_id:
                raise ConflictError("Ya existe una empresa con ese NIT.")
        company = await self._companies.update(company_id, clean, active)
        await self._audit.record(
            AuditEntry(
                action=AuditAction.COMPANY_UPDATED,
                actor_id=actor.user_id,
                actor_role=actor.role,
                company_id=company.id,
                resource_type="company",
                resource_id=company.id,
                details={"active": active},
            )
        )
        await self._uow.commit()
        return company
