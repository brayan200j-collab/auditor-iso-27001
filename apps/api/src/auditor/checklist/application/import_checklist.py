from __future__ import annotations

from dataclasses import dataclass

from auditor.checklist.application.definitions import ChecklistDefinition
from auditor.checklist.application.ports import ChecklistRepository
from auditor.checklist.domain.entities import ChecklistVersion
from auditor.shared.application.ports import UnitOfWork


@dataclass(frozen=True, slots=True)
class ImportResult:
    version: ChecklistVersion
    created: bool


class ImportChecklist:
    """Creates and publishes a checklist version from a definition.

    Idempotent per version number: an existing version is returned unchanged.
    """

    def __init__(self, repository: ChecklistRepository, uow: UnitOfWork) -> None:
        self._repository = repository
        self._uow = uow

    async def execute(self, definition: ChecklistDefinition) -> ImportResult:
        existing = await self._repository.get_by_number(definition.version)
        if existing is not None:
            return ImportResult(version=existing, created=False)
        draft = await self._repository.create_draft(definition, created_by=None)
        published = await self._repository.publish(draft.id)
        await self._uow.commit()
        return ImportResult(version=published, created=True)
