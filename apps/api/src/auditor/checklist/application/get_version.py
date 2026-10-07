from __future__ import annotations

from uuid import UUID

from auditor.checklist.application.ports import ChecklistRepository
from auditor.checklist.domain.entities import ChecklistVersion
from auditor.identity.public import Permission, authorize
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.errors import ResourceNotFoundError


class GetChecklistVersion:
    def __init__(self, checklists: ChecklistRepository) -> None:
        self._checklists = checklists

    async def execute(self, actor: Actor, version_id: UUID) -> ChecklistVersion:
        authorize(actor, Permission.MANAGE_CHECKLIST)
        version = await self._checklists.get(version_id)
        if version is None:
            raise ResourceNotFoundError()
        return version
