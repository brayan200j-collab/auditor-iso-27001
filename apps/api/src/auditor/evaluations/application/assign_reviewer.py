from __future__ import annotations

from uuid import UUID

from auditor.evaluations.application.access import EvaluationAccess
from auditor.evaluations.application.ports import EvaluationRepository, ReviewerDirectory
from auditor.identity.public import Permission
from auditor.shared.application.ports import AuditLogger, UnitOfWork
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.audit import AuditAction, AuditEntry
from auditor.shared.domain.errors import InvalidStateTransitionError, ValidationFailedError


class AssignReviewer:
    def __init__(
        self,
        access: EvaluationAccess,
        evaluations: EvaluationRepository,
        reviewers: ReviewerDirectory,
        audit: AuditLogger,
        uow: UnitOfWork,
    ) -> None:
        self._access = access
        self._evaluations = evaluations
        self._reviewers = reviewers
        self._audit = audit
        self._uow = uow

    async def execute(self, actor: Actor, evaluation_id: UUID, reviewer_id: UUID) -> None:
        evaluation = await self._access.require(actor, evaluation_id, Permission.ASSIGN_REVIEWER)
        if evaluation.is_locked:
            raise InvalidStateTransitionError("Una evaluación aprobada no se puede reasignar.")
        if not await self._reviewers.is_active_reviewer(reviewer_id):
            raise ValidationFailedError("La persona seleccionada no es un revisor activo.")
        await self._evaluations.set_reviewer(evaluation.id, reviewer_id)
        await self._audit.record(
            AuditEntry(
                action=AuditAction.REVIEWER_ASSIGNED,
                actor_id=actor.user_id,
                actor_role=actor.role,
                company_id=evaluation.company_id,
                resource_type="evaluation",
                resource_id=evaluation.id,
                details={"reviewer_id": str(reviewer_id)},
            )
        )
        await self._uow.commit()
