from __future__ import annotations

from uuid import UUID

from auditor.evaluations.application.access import EvaluationAccess
from auditor.evaluations.application.ports import ConsentRepository
from auditor.evaluations.domain.consent import CURRENT_CONSENT
from auditor.evaluations.domain.status import EvaluationStatus
from auditor.identity.public import Permission
from auditor.shared.application.ports import AuditLogger, UnitOfWork
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.audit import AuditAction, AuditEntry
from auditor.shared.domain.errors import InvalidStateTransitionError, ValidationFailedError

_OPEN_FOR_DOCUMENTS = {
    EvaluationStatus.DRAFT,
    EvaluationStatus.RECEIVED,
    EvaluationStatus.REJECTED,
}


class GiveConsent:
    """Records explicit, versioned consent before documents can be uploaded. Idempotent."""

    def __init__(
        self,
        access: EvaluationAccess,
        consents: ConsentRepository,
        audit: AuditLogger,
        uow: UnitOfWork,
    ) -> None:
        self._access = access
        self._consents = consents
        self._audit = audit
        self._uow = uow

    async def execute(self, actor: Actor, evaluation_id: UUID, version: str) -> None:
        evaluation = await self._access.require(actor, evaluation_id, Permission.UPLOAD_DOCUMENTS)
        if version != CURRENT_CONSENT.version:
            raise ValidationFailedError("La versión del consentimiento no es la vigente.")
        if evaluation.status not in _OPEN_FOR_DOCUMENTS:
            raise InvalidStateTransitionError()
        if await self._consents.has_consent(evaluation.id, actor.user_id, version):
            return
        await self._consents.add(evaluation.id, actor.user_id, version, CURRENT_CONSENT.sha256)
        await self._audit.record(
            AuditEntry(
                action=AuditAction.CONSENT_GIVEN,
                actor_id=actor.user_id,
                actor_role=actor.role,
                company_id=evaluation.company_id,
                resource_type="evaluation",
                resource_id=evaluation.id,
                details={"version": version},
            )
        )
        await self._uow.commit()
