"""Applies state-machine transitions, persists them atomically and records them in the audit trail.

Shared by this module's use cases and, through `auditor.evaluations.public`, by the documents,
analysis and review modules.
"""

from __future__ import annotations

from uuid import UUID

from auditor.evaluations.application.ports import AnalysisRunRepository, EvaluationRepository
from auditor.evaluations.domain.evaluation import AnalysisRun, Evaluation, FailureReason
from auditor.evaluations.domain.scope import AllEvaluations
from auditor.evaluations.domain.state_machine import Party, Trigger
from auditor.shared.application.ports import AuditLogger, Clock
from auditor.shared.domain.audit import AuditAction, AuditEntry, AuditOutcome, AuditValue

_AUDIT_ACTION: dict[Trigger, AuditAction] = {
    Trigger.START_ANALYSIS: AuditAction.PROCESSING_STARTED,
    Trigger.ANALYSIS_COMPLETED: AuditAction.PROCESSING_FINISHED,
    Trigger.PROCESSING_FAILED: AuditAction.PROCESSING_FAILED,
    Trigger.RETRY_EXTRACTION: AuditAction.PROCESSING_RETRIED,
    Trigger.RETRY_ANALYSIS: AuditAction.PROCESSING_RETRIED,
    Trigger.APPROVE: AuditAction.EVALUATION_APPROVED,
    Trigger.REJECT: AuditAction.EVALUATION_REJECTED,
}


class EvaluationLifecycle:
    def __init__(
        self,
        evaluations: EvaluationRepository,
        runs: AnalysisRunRepository,
        audit: AuditLogger,
        clock: Clock,
    ) -> None:
        self._evaluations = evaluations
        self._runs = runs
        self._audit = audit
        self._clock = clock

    async def transition(
        self,
        evaluation: Evaluation,
        trigger: Trigger,
        party: Party,
        *,
        actor_id: UUID | None = None,
        actor_role: str | None = None,
        reason: str | None = None,
        failure: FailureReason | None = None,
        details: dict[str, AuditValue] | None = None,
    ) -> Evaluation:
        """Validates and persists one transition. The caller commits the unit of work."""
        updated = evaluation.apply(
            trigger, party, self._clock.now(), actor_id=actor_id, reason=reason, failure=failure
        )
        await self._evaluations.save(updated, expected_status=evaluation.status)
        if trigger is Trigger.NEW_DOCUMENT_AFTER_REJECTION:
            await self._runs.add(updated.id, updated.current_run_number)
        action = _AUDIT_ACTION.get(trigger)
        if action is not None:
            await self._audit.record(
                AuditEntry(
                    action=action,
                    outcome=(
                        AuditOutcome.FAILURE
                        if trigger is Trigger.PROCESSING_FAILED
                        else AuditOutcome.SUCCESS
                    ),
                    actor_id=actor_id,
                    actor_role=actor_role or party.value,
                    company_id=updated.company_id,
                    resource_type="evaluation",
                    resource_id=updated.id,
                    details={
                        "from": evaluation.status.value,
                        "to": updated.status.value,
                        **({"failure": failure.value} if failure else {}),
                        **(details or {}),
                    },
                )
            )
        return updated

    async def current_run(self, evaluation: Evaluation) -> AnalysisRun:
        return await self._runs.current(evaluation)

    async def load_for_system(self, evaluation_id: UUID) -> Evaluation | None:
        """Unscoped load for background jobs (never reachable from an HTTP request)."""
        return await self._evaluations.get(evaluation_id, AllEvaluations())

    async def lock(self, evaluation_id: UUID) -> None:
        await self._evaluations.lock(evaluation_id)

    async def bind_checklist(self, run: AnalysisRun, checklist_version_id: UUID) -> None:
        await self._runs.bind_checklist(run.id, checklist_version_id)

    async def get_run(self, run_id: UUID) -> AnalysisRun | None:
        return await self._runs.get(run_id)

    async def mark_run_started(self, run: AnalysisRun) -> None:
        await self._runs.mark_started(run.id)

    async def mark_run_finished(self, run: AnalysisRun) -> None:
        await self._runs.mark_finished(run.id)
