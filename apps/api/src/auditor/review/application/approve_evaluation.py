from __future__ import annotations

from collections.abc import Awaitable, Callable
from uuid import UUID

from auditor.analysis.public import FindingRepository
from auditor.evaluations.public import (
    Evaluation,
    EvaluationAccess,
    EvaluationLifecycle,
    EvaluationStatus,
    Party,
    Trigger,
)
from auditor.identity.public import Permission
from auditor.review.application.ports import FinalFindingRepository
from auditor.shared.application.ports import UnitOfWork
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.errors import InvalidStateTransitionError, ValidationFailedError

AfterApproval = Callable[[Evaluation, Actor], Awaitable[None]]


async def _nothing(_evaluation: Evaluation, _actor: Actor) -> None:
    return None


class ApproveEvaluation:
    """PENDING_REVIEW → APPROVED once every finding of the run has been reviewed.

    Approval is final (the evaluation becomes immutable) and triggers the report generation.
    """

    def __init__(
        self,
        access: EvaluationAccess,
        lifecycle: EvaluationLifecycle,
        ai_findings: FindingRepository,
        finals: FinalFindingRepository,
        uow: UnitOfWork,
        after_approval: AfterApproval = _nothing,
    ) -> None:
        self._access = access
        self._lifecycle = lifecycle
        self._ai_findings = ai_findings
        self._finals = finals
        self._uow = uow
        self._after_approval = after_approval

    async def execute(self, actor: Actor, evaluation_id: UUID) -> Evaluation:
        evaluation = await self._access.require(actor, evaluation_id, Permission.DECIDE_EVALUATION)
        if evaluation.status is not EvaluationStatus.PENDING_REVIEW:
            raise InvalidStateTransitionError()
        await self._lifecycle.lock(evaluation.id)
        run = await self._lifecycle.current_run(evaluation)
        findings = {finding.id for finding in await self._ai_findings.list_for_run(run.id)}
        reviewed = {final.ai_finding_id for final in await self._finals.list_for_run(run.id)}
        pending = len(findings - reviewed)
        if not findings or pending:
            raise ValidationFailedError(
                f"Aún hay {pending} hallazgo(s) sin revisar. Revísalos antes de aprobar."
            )
        approved = await self._lifecycle.transition(
            evaluation,
            Trigger.APPROVE,
            Party.REVIEWER,
            actor_id=actor.user_id,
            actor_role=actor.role,
            details={"findings": len(findings)},
        )
        await self._after_approval(approved, actor)
        await self._uow.commit()
        return approved
