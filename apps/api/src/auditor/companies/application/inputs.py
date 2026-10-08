from __future__ import annotations

from dataclasses import dataclass

from auditor.companies.application.ports import CompanyData
from auditor.companies.domain.rules import normalize_name, normalize_tax_id


@dataclass(frozen=True, slots=True)
class CompanyInput:
    name: str
    tax_id: str | None
    sector: str | None
    city: str | None


def clean_company_input(data: CompanyInput) -> CompanyData:
    def optional(value: str | None) -> str | None:
        return " ".join(value.split()) or None if value else None

    return CompanyData(
        name=normalize_name(data.name),
        tax_id=normalize_tax_id(data.tax_id),
        sector=optional(data.sector),
        city=optional(data.city),
    )
