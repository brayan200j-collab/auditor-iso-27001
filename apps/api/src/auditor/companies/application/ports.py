from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from auditor.companies.domain.company import Company
from auditor.shared.domain.pagination import Page, PageRequest


@dataclass(frozen=True, slots=True)
class CompanyData:
    name: str
    tax_id: str | None
    sector: str | None
    city: str | None


class CompanyRepository(Protocol):
    async def get(self, company_id: UUID) -> Company | None: ...

    async def get_by_tax_id(self, tax_id: str) -> Company | None: ...

    async def list(self, search: str | None, page: PageRequest) -> Page[Company]: ...

    async def add(self, data: CompanyData) -> Company: ...

    async def update(self, company_id: UUID, data: CompanyData, active: bool) -> Company: ...
