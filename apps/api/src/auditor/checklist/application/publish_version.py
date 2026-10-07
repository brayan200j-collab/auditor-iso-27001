from __future__ import annotations

from uuid import UUID

from auditor.checklist.application.ports import ChecklistRepository
from auditor.checklist.domain.entities import ChecklistVersion
from auditor.identity.public import Permission, authorize
from auditor.shared.application.ports import AuditLogger, UnitOfWork
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.audit import AuditAction, AuditEntry
from auditor.shared.domain.errors import ValidationFailedError


class PublishChecklistVersion:
    """Publishes the draft. New evaluations use it; running ones keep their bound version."""

    def __init__(
        self, checklists: ChecklistRepository, audit: AuditLogger, uow: UnitOfWork
    ) -> None:
        self._checklists = checklists
        self._audit = audit
        self._uow = uow

    async def execute(self, actor: Actor, version_id: UUID) -> ChecklistVersion:
        authorize(actor, Permission.MANAGE_CHECKLIST)
        draft = await self._checklists.get(version_id)
        if draft is not None and not draft.active_items:
            raise ValidationFailedError("La versión debe tener al menos un criterio activo.")
        version = await self._checklists.publish(version_id)
        await self._audit.record(
            AuditEntry(
                action=AuditAction.CHECKLIST_VERSION_PUBLISHED,
                actor_id=actor.user_id,
                actor_role=actor.role,
                resource_type="checklist_version",
                resource_id=version.id,
                details={"version": version.version, "active_items": len(version.active_items)},
            )
        )
        await self._uow.commit()
        return version
