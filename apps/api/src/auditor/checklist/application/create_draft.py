from __future__ import annotations

from auditor.checklist.application.copying import copy_as
from auditor.checklist.application.ports import ChecklistRepository
from auditor.checklist.domain.entities import ChecklistVersion
from auditor.identity.public import Permission, authorize
from auditor.shared.application.ports import AuditLogger, UnitOfWork
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.audit import AuditAction, AuditEntry
from auditor.shared.domain.errors import ConflictError


class CreateChecklistDraft:
    """Starts a new version as a copy of the latest published one. Only one draft at a time."""

    def __init__(
        self, checklists: ChecklistRepository, audit: AuditLogger, uow: UnitOfWork
    ) -> None:
        self._checklists = checklists
        self._audit = audit
        self._uow = uow

    async def execute(self, actor: Actor) -> ChecklistVersion:
        authorize(actor, Permission.MANAGE_CHECKLIST)
        if await self._checklists.draft() is not None:
            raise ConflictError("Ya existe una versión en borrador. Publícala antes de crear otra.")
        base = await self._checklists.latest_published()
        if base is None:
            raise ConflictError("No hay una versión publicada para copiar.")
        number = await self._checklists.next_version_number()
        draft = await self._checklists.create_draft(copy_as(base, number), actor.user_id)
        await self._audit.record(
            AuditEntry(
                action=AuditAction.CHECKLIST_VERSION_CREATED,
                actor_id=actor.user_id,
                actor_role=actor.role,
                resource_type="checklist_version",
                resource_id=draft.id,
                details={"version": number, "copied_from": base.version},
            )
        )
        await self._uow.commit()
        return draft
