from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.companies.application.ports import CompanyData
from auditor.companies.domain.company import Company
from auditor.companies.infrastructure.models import CompanyModel
from auditor.shared.domain.errors import ResourceNotFoundError
from auditor.shared.domain.pagination import Page, PageRequest
from auditor.shared.infrastructure.database import contains_pattern


def _to_company(model: CompanyModel) -> Company:
    return Company(
        id=model.id,
        name=model.name,
        tax_id=model.tax_id,
        sector=model.sector,
        city=model.city,
        active=model.active,
        created_at=model.created_at,
    )


class SqlCompanyRepository:
    """Company persistence. Also serves as the `CompanyDirectory` other modules depend on."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, company_id: UUID) -> Company | None:
        model = await self._session.get(CompanyModel, company_id)
        return _to_company(model) if model else None

    async def get_by_tax_id(self, tax_id: str) -> Company | None:
        model = await self._session.scalar(
            select(CompanyModel).where(CompanyModel.tax_id == tax_id.strip())
        )
        return _to_company(model) if model else None

    async def name_of(self, company_id: UUID) -> str | None:
        name: str | None = await self._session.scalar(
            select(CompanyModel.name).where(CompanyModel.id == company_id)
        )
        return name

    async def exists(self, company_id: UUID) -> bool:
        return await self.name_of(company_id) is not None

    async def names_of(self, ids: Iterable[UUID]) -> dict[UUID, str]:
        wanted = set(ids)
        if not wanted:
            return {}
        rows = await self._session.execute(
            select(CompanyModel.id, CompanyModel.name).where(CompanyModel.id.in_(wanted))
        )
        return dict(rows.all())

    async def list(self, search: str | None, page: PageRequest) -> Page[Company]:
        query = select(CompanyModel)
        if search:
            pattern = contains_pattern(search)
            query = query.where(
                or_(
                    func.lower(CompanyModel.name).like(pattern, escape="\\"),
                    CompanyModel.tax_id.like(pattern, escape="\\"),
                )
            )
        total = await self._session.scalar(select(func.count()).select_from(query.subquery()))
        models = await self._session.scalars(
            query.order_by(func.lower(CompanyModel.name)).offset(page.offset).limit(page.page_size)
        )
        return Page(
            items=[_to_company(model) for model in models],
            total=total or 0,
            page=page.page,
            page_size=page.page_size,
        )

    async def add(self, data: CompanyData) -> Company:
        model = CompanyModel(name=data.name, tax_id=data.tax_id, sector=data.sector, city=data.city)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_company(model)

    async def update(self, company_id: UUID, data: CompanyData, active: bool) -> Company:
        model = await self._session.get(CompanyModel, company_id)
        if model is None:
            raise ResourceNotFoundError()
        model.name = data.name
        model.tax_id = data.tax_id
        model.sector = data.sector
        model.city = data.city
        model.active = active
        model.updated_at = datetime.now(UTC)
        await self._session.flush()
        return _to_company(model)
