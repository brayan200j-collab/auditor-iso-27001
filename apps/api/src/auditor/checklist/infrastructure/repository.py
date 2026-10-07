from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.checklist.application.definitions import ChecklistDefinition
from auditor.checklist.domain.entities import (
    ChecklistItem,
    ChecklistVersion,
    ReferenceStatus,
    VersionStatus,
)
from auditor.checklist.infrastructure.models import ChecklistItemModel, ChecklistVersionModel
from auditor.shared.domain.errors import ConflictError, ResourceNotFoundError
from auditor.shared.domain.vocabulary import Level, Priority


def _item(model: ChecklistItemModel) -> ChecklistItem:
    return ChecklistItem(
        id=model.id,
        code=model.code,
        position=model.position,
        name=model.name,
        description=model.description,
        evaluation_question=model.evaluation_question,
        expected_evidence=model.expected_evidence,
        iso_reference=model.iso_reference or None,
        cis_reference=model.cis_reference or None,
        nist_reference=model.nist_reference or None,
        reference_status=ReferenceStatus(model.reference_status),
        keywords=tuple(model.keywords),
        priority=Priority(model.priority),
        risk_level=Level(model.risk_level),
        effort=Level(model.effort),
        active=model.active,
    )


class SqlChecklistRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _load(self, version: ChecklistVersionModel) -> ChecklistVersion:
        items = await self._session.scalars(
            select(ChecklistItemModel)
            .where(ChecklistItemModel.version_id == version.id)
            .order_by(ChecklistItemModel.position)
        )
        return ChecklistVersion(
            id=version.id,
            version=version.version,
            label=version.label,
            status=VersionStatus(version.status),
            published_at=version.published_at,
            items=tuple(_item(item) for item in items),
        )

    async def get_by_number(self, version: int) -> ChecklistVersion | None:
        model = await self._session.scalar(
            select(ChecklistVersionModel).where(ChecklistVersionModel.version == version)
        )
        return await self._load(model) if model else None

    async def get(self, version_id: UUID) -> ChecklistVersion | None:
        model = await self._session.get(ChecklistVersionModel, version_id)
        return await self._load(model) if model else None

    async def latest_published(self) -> ChecklistVersion | None:
        model = await self._session.scalar(
            select(ChecklistVersionModel)
            .where(ChecklistVersionModel.status == VersionStatus.PUBLISHED)
            .order_by(ChecklistVersionModel.version.desc())
            .limit(1)
        )
        return await self._load(model) if model else None

    async def list_versions(self) -> list[ChecklistVersion]:
        models = await self._session.scalars(
            select(ChecklistVersionModel).order_by(ChecklistVersionModel.version.desc())
        )
        return [await self._load(model) for model in models]

    async def next_version_number(self) -> int:
        current = await self._session.scalar(select(func.max(ChecklistVersionModel.version)))
        return (current or 0) + 1

    async def create_draft(
        self, definition: ChecklistDefinition, created_by: UUID | None
    ) -> ChecklistVersion:
        version = ChecklistVersionModel(
            version=definition.version,
            label=definition.label,
            status=VersionStatus.DRAFT,
            created_by=created_by,
        )
        self._session.add(version)
        await self._session.flush()
        self._add_items(version.id, definition)
        await self._session.flush()
        return await self._load(version)

    async def replace_draft_items(
        self, version_id: UUID, definition: ChecklistDefinition
    ) -> ChecklistVersion:
        version = await self._session.get(ChecklistVersionModel, version_id)
        if version is None:
            raise ResourceNotFoundError()
        if version.status != VersionStatus.DRAFT:
            raise ConflictError("Una versión publicada no se puede modificar.")
        existing = await self._session.scalars(
            select(ChecklistItemModel).where(ChecklistItemModel.version_id == version_id)
        )
        for item in existing:
            await self._session.delete(item)
        await self._session.flush()
        version.label = definition.label
        self._add_items(version_id, definition)
        await self._session.flush()
        return await self._load(version)

    async def publish(self, version_id: UUID) -> ChecklistVersion:
        result = await self._session.execute(
            update(ChecklistVersionModel)
            .where(
                ChecklistVersionModel.id == version_id,
                ChecklistVersionModel.status == VersionStatus.DRAFT,
            )
            .values(status=VersionStatus.PUBLISHED, published_at=datetime.now(UTC))
            .returning(ChecklistVersionModel.id)
        )
        if result.scalar_one_or_none() is None:
            raise ConflictError("La versión no existe o ya fue publicada.")
        model = await self._session.get(ChecklistVersionModel, version_id, populate_existing=True)
        if model is None:  # pragma: no cover - just updated
            raise ResourceNotFoundError()
        return await self._load(model)

    def _add_items(self, version_id: UUID, definition: ChecklistDefinition) -> None:
        for position, item in enumerate(definition.items, start=1):
            self._session.add(
                ChecklistItemModel(
                    version_id=version_id,
                    code=item.code,
                    position=position,
                    name=item.name,
                    description=item.description,
                    evaluation_question=item.evaluation_question,
                    expected_evidence=item.expected_evidence,
                    iso_reference=item.iso_reference or None,
                    cis_reference=item.cis_reference or None,
                    nist_reference=item.nist_reference or None,
                    reference_status=item.reference_status,
                    keywords=list(item.keywords),
                    priority=item.priority,
                    risk_level=item.risk_level,
                    effort=item.effort,
                    active=item.active,
                )
            )
