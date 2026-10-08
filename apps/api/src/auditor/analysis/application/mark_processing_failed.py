from __future__ import annotations

from auditor.evaluations.public import (
    PROCESSING_STATUSES,
    EvaluationLifecycle,
    FailureReason,
    Party,
    Trigger,
)
from auditor.shared.application.jobs import JobRecord
from auditor.shared.application.ports import UnitOfWork
from auditor.shared.domain.vocabulary import JobKind

_BY_REASON = {
    "INTERRUPTED": FailureReason.INTERRUPTED,
    "QUOTA_EXCEEDED": FailureReason.QUOTA_EXCEEDED,
}


def failure_for(job: JobRecord, reason: str) -> FailureReason:
    if reason in _BY_REASON:
        return _BY_REASON[reason]
    if job.kind is JobKind.EXTRACTION:
        return FailureReason.EXTRACTION_ERROR
    return FailureReason.ANALYSIS_ERROR


class MarkProcessingFailed:
    """Called when a job fails for good: the evaluation moves to FAILED with a friendly reason."""

    def __init__(self, lifecycle: EvaluationLifecycle, uow: UnitOfWork) -> None:
        self._lifecycle = lifecycle
        self._uow = uow

    async def execute(self, job: JobRecord, reason: str) -> None:
        evaluation = await self._lifecycle.load_for_system(job.evaluation_id)
        if evaluation is None or evaluation.status not in PROCESSING_STATUSES:
            return
        await self._lifecycle.transition(
            evaluation,
            Trigger.PROCESSING_FAILED,
            Party.SYSTEM,
            failure=failure_for(job, reason),
            details={"job_kind": job.kind.value},
        )
        await self._uow.commit()
