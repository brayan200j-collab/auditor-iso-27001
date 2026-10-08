from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import Field

from auditor.companies.application.create_company import CreateCompany
from auditor.companies.application.get_company import GetCompany
from auditor.companies.application.inputs import CompanyInput
from auditor.companies.application.list_companies import ListCompanies
from auditor.companies.application.update_company import UpdateCompany
from auditor.companies.domain.company import Company
from auditor.shared.api.dependencies import CurrentActor, use_case
from auditor.shared.api.pagination import PageParams
from auditor.shared.api.schemas import ERROR_RESPONSES, ApiModel, PageMeta, RequestModel

router = APIRouter(prefix="/api/v1/companies", tags=["companies"], responses=ERROR_RESPONSES)


class CompanyRequest(RequestModel):
    name: str = Field(min_length=2, max_length=200)
    tax_id: str | None = Field(
        default=None,
        pattern=r"^\d{5,15}(-\d)?$",
        description="NIT sin puntos ni espacios, con dígito de verificación opcional.",
    )
    sector: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, max_length=120)

    def to_input(self) -> CompanyInput:
        return CompanyInput(name=self.name, tax_id=self.tax_id, sector=self.sector, city=self.city)


class CompanyUpdateRequest(CompanyRequest):
    active: bool = True


class CompanyResponse(ApiModel):
    id: UUID
    name: str
    tax_id: str | None
    sector: str | None
    city: str | None
    active: bool
    created_at: datetime

    @classmethod
    def of(cls, company: Company) -> CompanyResponse:
        return cls(
            id=company.id,
            name=company.name,
            tax_id=company.tax_id,
            sector=company.sector,
            city=company.city,
            active=company.active,
            created_at=company.created_at,
        )


class CompanyPage(ApiModel):
    items: list[CompanyResponse]
    meta: PageMeta


@router.get("", response_model=CompanyPage, summary="Listar empresas")
async def list_companies(
    actor: CurrentActor,
    page: PageParams,
    list_use_case: Annotated[ListCompanies, Depends(use_case(ListCompanies))],
    search: Annotated[str | None, Query(max_length=100)] = None,
) -> CompanyPage:
    result = await list_use_case.execute(actor, search, page)
    return CompanyPage(
        items=[CompanyResponse.of(item) for item in result.items],
        meta=PageMeta(total=result.total, page=result.page, page_size=result.page_size),
    )


@router.post(
    "",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear empresa",
)
async def create_company(
    actor: CurrentActor,
    body: CompanyRequest,
    create: Annotated[CreateCompany, Depends(use_case(CreateCompany))],
) -> CompanyResponse:
    return CompanyResponse.of(await create.execute(actor, body.to_input()))


@router.get("/{company_id}", response_model=CompanyResponse, summary="Detalle de empresa")
async def get_company(
    actor: CurrentActor,
    company_id: UUID,
    get: Annotated[GetCompany, Depends(use_case(GetCompany))],
) -> CompanyResponse:
    return CompanyResponse.of(await get.execute(actor, company_id))


@router.patch("/{company_id}", response_model=CompanyResponse, summary="Actualizar empresa")
async def update_company(
    actor: CurrentActor,
    company_id: UUID,
    body: CompanyUpdateRequest,
    update: Annotated[UpdateCompany, Depends(use_case(UpdateCompany))],
) -> CompanyResponse:
    return CompanyResponse.of(await update.execute(actor, company_id, body.to_input(), body.active))
