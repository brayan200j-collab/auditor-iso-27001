from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import Field

from auditor.checklist.application.create_draft import CreateChecklistDraft
from auditor.checklist.application.definitions import ChecklistItemDefinition
from auditor.checklist.application.get_version import GetChecklistVersion
from auditor.checklist.application.list_versions import ListChecklistVersions
from auditor.checklist.application.publish_version import PublishChecklistVersion
from auditor.checklist.application.update_item import UpdateChecklistItem
from auditor.checklist.domain.entities import (
    ChecklistItem,
    ChecklistVersion,
    ReferenceStatus,
    VersionStatus,
)
from auditor.shared.api.dependencies import CurrentActor, use_case
from auditor.shared.api.schemas import ERROR_RESPONSES, ApiModel, RequestModel
from auditor.shared.domain.vocabulary import Level, Priority

router = APIRouter(prefix="/api/v1/checklists", tags=["checklist"], responses=ERROR_RESPONSES)


class ChecklistItemResponse(ApiModel):
    id: UUID
    code: str
    position: int
    name: str
    description: str
    evaluation_question: str
    expected_evidence: str
    iso_reference: str | None
    cis_reference: str | None
    nist_reference: str | None
    reference_status: ReferenceStatus
    keywords: list[str]
    priority: Priority
    risk_level: Level
    effort: Level
    active: bool

    @classmethod
    def of(cls, item: ChecklistItem) -> ChecklistItemResponse:
        return cls(
            id=item.id,
            code=item.code,
            position=item.position,
            name=item.name,
            description=item.description,
            evaluation_question=item.evaluation_question,
            expected_evidence=item.expected_evidence,
            iso_reference=item.iso_reference,
            cis_reference=item.cis_reference,
            nist_reference=item.nist_reference,
            reference_status=item.reference_status,
            keywords=list(item.keywords),
            priority=item.priority,
            risk_level=item.risk_level,
            effort=item.effort,
            active=item.active,
        )


class ChecklistVersionSummary(ApiModel):
    id: UUID
    version: int
    label: str
    status: VersionStatus
    published_at: datetime | None
    item_count: int
    active_item_count: int

    @classmethod
    def of(cls, version: ChecklistVersion) -> ChecklistVersionSummary:
        return cls(
            id=version.id,
            version=version.version,
            label=version.label,
            status=version.status,
            published_at=version.published_at,
            item_count=len(version.items),
            active_item_count=len(version.active_items),
        )


class ChecklistVersionResponse(ChecklistVersionSummary):
    items: list[ChecklistItemResponse]

    @classmethod
    def of(cls, version: ChecklistVersion) -> ChecklistVersionResponse:
        summary = ChecklistVersionSummary.of(version)
        return cls(
            **summary.model_dump(), items=[ChecklistItemResponse.of(i) for i in version.items]
        )


class ChecklistItemUpdateRequest(RequestModel):
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=10, max_length=2000)
    evaluation_question: str = Field(min_length=10, max_length=2000)
    expected_evidence: str = Field(min_length=10, max_length=2000)
    iso_reference: str = Field(default="", max_length=80)
    cis_reference: str = Field(default="", max_length=80)
    nist_reference: str = Field(default="", max_length=80)
    reference_status: ReferenceStatus = ReferenceStatus.DRAFT
    keywords: list[str] = Field(min_length=1, max_length=20)
    priority: Priority
    risk_level: Level
    effort: Level
    active: bool = True


@router.get("", response_model=list[ChecklistVersionSummary], summary="Versiones del checklist")
async def list_versions(
    actor: CurrentActor,
    list_use_case: Annotated[ListChecklistVersions, Depends(use_case(ListChecklistVersions))],
) -> list[ChecklistVersionSummary]:
    return [ChecklistVersionSummary.of(v) for v in await list_use_case.execute(actor)]


@router.post(
    "",
    response_model=ChecklistVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un borrador a partir de la versión publicada",
)
async def create_draft(
    actor: CurrentActor,
    create: Annotated[CreateChecklistDraft, Depends(use_case(CreateChecklistDraft))],
) -> ChecklistVersionResponse:
    return ChecklistVersionResponse.of(await create.execute(actor))


@router.get(
    "/{version_id}", response_model=ChecklistVersionResponse, summary="Criterios de una versión"
)
async def get_version(
    actor: CurrentActor,
    version_id: UUID,
    get: Annotated[GetChecklistVersion, Depends(use_case(GetChecklistVersion))],
) -> ChecklistVersionResponse:
    return ChecklistVersionResponse.of(await get.execute(actor, version_id))


@router.put(
    "/{version_id}/items/{code}",
    response_model=ChecklistVersionResponse,
    summary="Editar un criterio del borrador",
)
async def update_item(
    actor: CurrentActor,
    version_id: UUID,
    code: str,
    body: ChecklistItemUpdateRequest,
    update: Annotated[UpdateChecklistItem, Depends(use_case(UpdateChecklistItem))],
) -> ChecklistVersionResponse:
    definition = ChecklistItemDefinition(code=code, **body.model_dump())
    return ChecklistVersionResponse.of(await update.execute(actor, version_id, definition))


@router.post(
    "/{version_id}/publish",
    response_model=ChecklistVersionResponse,
    summary="Publicar el borrador",
)
async def publish(
    actor: CurrentActor,
    version_id: UUID,
    publish_use_case: Annotated[
        PublishChecklistVersion, Depends(use_case(PublishChecklistVersion))
    ],
) -> ChecklistVersionResponse:
    return ChecklistVersionResponse.of(await publish_use_case.execute(actor, version_id))
