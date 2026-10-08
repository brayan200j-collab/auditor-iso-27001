"""Authorization chain for everything attached to an evaluation (CLAUDE.md section 8):
authentication → permission → company/assignment scope → evaluation → (document, finding, report).

Other modules must load evaluations through `EvaluationAccess.require`, never directly.
"""

from __future__ import annotations

from uuid import UUID

from auditor.evaluations.application.ports import EvaluationRepository
from auditor.evaluations.domain.evaluation import Evaluation
from auditor.evaluations.domain.scope import (
    AllEvaluations,
    AssignedEvaluations,
    CompanyEvaluations,
    DataScope,
)
from auditor.identity.public import Permission, Scope, scope_for
from auditor.shared.application.ports import AuditLogger
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.audit import AuditAction, AuditEntry, AuditOutcome
from auditor.shared.domain.errors import ForbiddenError, ResourceNotFoundError


def data_scope(actor: Actor, permission: Permission) -> DataScope:
    scope = scope_for(actor, permission)
    if scope is Scope.ALL:
        return AllEvaluations()
    if scope is Scope.ASSIGNED:
        return AssignedEvaluations(reviewer_id=actor.user_id)
    if scope is Scope.OWN_COMPANY and actor.company_id is not None:
        return CompanyEvaluations(company_id=actor.company_id)
    raise ForbiddenError(detail=f"{actor.role} lacks {permission}")


class EvaluationAccess:
    def __init__(self, evaluations: EvaluationRepository, audit: AuditLogger) -> None:
        self._evaluations = evaluations
        self._audit = audit

    async def require(
        self, actor: Actor, evaluation_id: UUID, permission: Permission
    ) -> Evaluation:
        """Loads the evaluation within the actor's scope or fails with a generic 404/403.

        Attempts on evaluations that exist outside the actor's scope are audited as
        ACCESS_DENIED; the response never reveals whether the evaluation exists.
        """
        try:
            scope = data_scope(actor, permission)
        except ForbiddenError:
            await self._denied(actor, evaluation_id, permission, "permission")
            raise
        evaluation = await self._evaluations.get(evaluation_id, scope)
        if evaluation is None:
            if await self._evaluations.exists(evaluation_id):
                await self._denied(actor, evaluation_id, permission, "scope")
            raise ResourceNotFoundError()
        return evaluation

    async def _denied(
        self, actor: Actor, evaluation_id: UUID, permission: Permission, reason: str
    ) -> None:
        await self._audit.record_immediately(
            AuditEntry(
                action=AuditAction.ACCESS_DENIED,
                outcome=AuditOutcome.DENIED,
                actor_id=actor.user_id,
                actor_role=actor.role,
                company_id=actor.company_id,
                resource_type="evaluation",
                resource_id=evaluation_id,
                details={"permission": permission.value, "reason": reason},
            )
        )
