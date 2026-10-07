from __future__ import annotations

from uuid import UUID

from auditor.evaluations.application.ports import (
    AnalysisRunRepository,
    EvaluationRepository,
    NewEvaluation,
)
from auditor.evaluations.domain.evaluation import Evaluation, validate_title
from auditor.identity.public import Permission, authorize
from auditor.shared.application.ports import AuditLogger, UnitOfWork
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.audit import AuditAction, AuditEntry, AuditOutcome
from auditor.shared.domain.errors import ForbiddenError, QuotaExceededError

QUOTA_MESSAGE = "Tu empresa alcanzó el número máximo de evaluaciones permitidas en el piloto."


class CreateEvaluation:
    def __init__(
        self,
        evaluations: EvaluationRepository,
        runs: AnalysisRunRepository,
        audit: AuditLogger,
        uow: UnitOfWork,
        max_per_company: int,
    ) -> None:
        self._evaluations = evaluations
        self._runs = runs
        self._audit = audit
        self._uow = uow
        self._max_per_company = max_per_company

    async def execute(self, actor: Actor, title: str) -> Evaluation:
        authorize(actor, Permission.CREATE_EVALUATION)
        if actor.company_id is None:
            raise ForbiddenError(detail="SME user without company")
        clean_title = validate_title(title)
        await self._enforce_quota(actor, actor.company_id)
        evaluation = await self._evaluations.add(
            NewEvaluation(company_id=actor.company_id, created_by=actor.user_id, title=clean_title)
        )
        await self._runs.add(evaluation.id, run_number=1)
        await self._audit.record(
            AuditEntry(
                action=AuditAction.EVALUATION_CREATED,
                actor_id=actor.user_id,
                actor_role=actor.role,
                company_id=evaluation.company_id,
                resource_type="evaluation",
                resource_id=evaluation.id,
            )
        )
        await self._uow.commit()
        return evaluation

    async def _enforce_quota(self, actor: Actor, company_id: UUID) -> None:
        used = await self._evaluations.count_for_company(company_id)
        if used < self._max_per_company:
            return
        await self._audit.record_immediately(
            AuditEntry(
                action=AuditAction.QUOTA_EXCEEDED,
                outcome=AuditOutcome.DENIED,
                actor_id=actor.user_id,
                actor_role=actor.role,
                company_id=company_id,
                resource_type="evaluation",
                details={"quota": "MAX_EVALUATIONS_PER_COMPANY", "limit": self._max_per_company},
            )
        )
        raise QuotaExceededError(QUOTA_MESSAGE)
