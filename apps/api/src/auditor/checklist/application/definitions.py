"""Validated definition of a checklist version (used by the YAML seed and by administrators)."""

from __future__ import annotations

from typing import Annotated, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from auditor.checklist.domain.entities import ReferenceStatus, is_valid_code
from auditor.shared.domain.vocabulary import Level, Priority

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=2000)]
Reference = Annotated[str, StringConstraints(strip_whitespace=True, max_length=80)]
Keyword = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=80)]


class ChecklistItemDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    name: ShortText
    description: LongText
    evaluation_question: LongText
    expected_evidence: LongText
    iso_reference: Reference = ""
    cis_reference: Reference = ""
    nist_reference: Reference = ""
    reference_status: ReferenceStatus = ReferenceStatus.DRAFT
    keywords: list[Keyword] = Field(min_length=1, max_length=20)
    priority: Priority
    risk_level: Level
    effort: Level
    active: bool = True

    @field_validator("code")
    @classmethod
    def _code_format(cls, value: str) -> str:
        if not is_valid_code(value):
            raise ValueError("code must look like ISO-01")
        return value

    @field_validator("cis_reference")
    @classmethod
    def _no_cis_shorthand(cls, value: str) -> str:
        if value.upper().startswith("CIS-"):
            raise ValueError("use safeguard identifiers such as 1.1, never CIS-1")
        return value


class ChecklistDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: int = Field(ge=1)
    label: ShortText
    items: list[ChecklistItemDefinition] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def _unique_codes(self) -> Self:
        codes = [item.code for item in self.items]
        if len(codes) != len(set(codes)):
            raise ValueError("checklist item codes must be unique")
        return self
