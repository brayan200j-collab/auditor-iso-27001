from __future__ import annotations

from uuid import UUID

from auditor.checklist.application.definitions import ChecklistItemDefinition
from auditor.checklist.application.ports import ChecklistRepository
from auditor.checklist.domain.entities import ChecklistVersion
from auditor.identity.public import Permission, authorize
from auditor.shared.application.ports import UnitOfWork
from auditor.shared.domain.actor import Actor


class UpdateChecklistItem:
    """Edits one criterion of the draft version (published versions are immutable)."""

    def __init__(self, checklists: ChecklistRepository, uow: UnitOfWork) -> None:
        self._checklists = checklists
        self._uow = uow

    async def execute(
        self, actor: Actor, version_id: UUID, item: ChecklistItemDefinition
    ) -> ChecklistVersion:
        authorize(actor, Permission.MANAGE_CHECKLIST)
        version = await self._checklists.update_item(version_id, item)
        await self._uow.commit()
        return version
