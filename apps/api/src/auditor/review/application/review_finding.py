from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from auditor.analysis.public import FindingRepository
from auditor.evaluations.public import EvaluationAccess, EvaluationLifecycle, EvaluationStatus
from auditor.identity.public import Permission
from auditor.review.application.ports import (
    FinalFindingRepository,
    FindingKey,
    HumanReviewEntry,
    HumanReviewRepository,
)
from auditor.review.application.values import ai_values, verified_evidence
from auditor.review.domain.review import (
    FinalFinding,
    FinalValues,
    ReviewAction,
    approve,
    discard,
    edit,
)
from auditor.shared.application.ports import AuditLogger, Clock, UnitOfWork
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.audit import AuditAction, AuditEntry
from auditor.shared.domain.errors import InvalidStateTransitionError, ResourceNotFoundError


@dataclass(frozen=True, slots=True)
class ReviewRequest:
    action: ReviewAction
    comment: str | None = None
    edited: FinalValues | None = None


class ReviewFinding:
    """Approve, edit or discard one AI finding. The AI finding itself is never modified."""

    def __init__(
        self,
        access: EvaluationAccess,
        lifecycle: EvaluationLifecycle,
        ai_findings: FindingRepository,
        finals: FinalFindingRepository,
        reviews: HumanReviewRepository,
        audit: AuditLogger,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._access = access
        self._lifecycle = lifecycle
        self._ai_findings = ai_findings
        self._finals = finals
        self._reviews = reviews
        self._audit = audit
        self._uow = uow
        self._clock = clock

    async def execute(self, actor: Actor, finding_id: UUID, request: ReviewRequest) -> FinalFinding:
        finding = await self._ai_findings.get(finding_id)
        if finding is None:
            raise ResourceNotFoundError()
        evaluation = await self._access.require(
            actor, finding.evaluation_id, Permission.REVIEW_FINDINGS
        )
        if evaluation.status is not EvaluationStatus.PENDING_REVIEW:
            raise InvalidStateTransitionError(
                "Los hallazgos solo se pueden revisar mientras la evaluación "
                "está pendiente de revisión."
            )
        run = await self._lifecycle.current_run(evaluation)
        if finding.analysis_run_id != run.id:
            raise InvalidStateTransitionError("El hallazgo pertenece a un análisis anterior.")

        original = ai_values(finding)
        evidence = verified_evidence(finding)
        if request.action is ReviewAction.APPROVE:
            decision = approve(original, evidence, request.comment)
        elif request.action is ReviewAction.EDIT:
            decision = edit(request.edited or original, evidence, request.comment)
        else:
            decision = discard(original, request.comment)

        previous = await self._finals.get_for_ai_finding(finding.id)
        key = FindingKey(
            ai_finding_id=finding.id,
            evaluation_id=finding.evaluation_id,
            analysis_run_id=finding.analysis_run_id,
            checklist_item_id=finding.checklist_item_id,
            criterion_code=finding.criterion_code,
        )
        final = await self._finals.save(key, decision, actor.user_id, self._clock.now())
        await self._reviews.add(
            HumanReviewEntry(
                ai_finding_id=finding.id,
                evaluation_id=finding.evaluation_id,
                reviewer_id=actor.user_id,
                action=decision.action.value,
                comment=decision.comment,
                previous_values=(previous.values if previous else original).as_dict(),
                new_values=decision.values.as_dict(),
            )
        )
        await self._audit.record(
            AuditEntry(
                action=AuditAction.FINDING_REVIEWED,
                actor_id=actor.user_id,
                actor_role=actor.role,
                company_id=evaluation.company_id,
                resource_type="ai_finding",
                resource_id=finding.id,
                details={"criterion": finding.criterion_code, "action": decision.action.value},
            )
        )
        await self._uow.commit()
        return final
