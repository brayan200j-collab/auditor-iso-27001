from __future__ import annotations

from auditor.checklist.application.ports import ChecklistRepository
from auditor.checklist.domain.entities import ChecklistVersion
from auditor.identity.public import Permission, authorize
from auditor.shared.domain.actor import Actor


class ListChecklistVersions:
    def __init__(self, checklists: ChecklistRepository) -> None:
        self._checklists = checklists

    async def execute(self, actor: Actor) -> list[ChecklistVersion]:
        authorize(actor, Permission.MANAGE_CHECKLIST)
        return await self._checklists.list_versions()
