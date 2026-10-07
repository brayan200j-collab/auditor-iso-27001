from __future__ import annotations

from uuid import UUID

from auditor.evaluations.public import (
    Evaluation,
    EvaluationAccess,
    EvaluationLifecycle,
    Party,
    Trigger,
)
from auditor.identity.public import Permission
from auditor.shared.application.ports import UnitOfWork
from auditor.shared.domain.actor import Actor


class RejectEvaluation:
    """PENDING_REVIEW → REJECTED with a mandatory reason the company will see."""

    def __init__(
        self, access: EvaluationAccess, lifecycle: EvaluationLifecycle, uow: UnitOfWork
    ) -> None:
        self._access = access
        self._lifecycle = lifecycle
        self._uow = uow

    async def execute(self, actor: Actor, evaluation_id: UUID, reason: str) -> Evaluation:
        evaluation = await self._access.require(actor, evaluation_id, Permission.DECIDE_EVALUATION)
        rejected = await self._lifecycle.transition(
            evaluation,
            Trigger.REJECT,
            Party.REVIEWER,
            actor_id=actor.user_id,
            actor_role=actor.role,
            reason=reason,
        )
        await self._uow.commit()
        return rejected
