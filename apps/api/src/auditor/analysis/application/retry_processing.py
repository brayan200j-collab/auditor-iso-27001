from __future__ import annotations

from uuid import UUID

from auditor.documents.public import DocumentRepository
from auditor.evaluations.public import (
    Evaluation,
    EvaluationAccess,
    EvaluationLifecycle,
    EvaluationStatus,
    Party,
    Trigger,
)
from auditor.identity.public import Permission
from auditor.shared.application.jobs import JobRepository, JobRunner
from auditor.shared.application.ports import UnitOfWork
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.errors import InvalidStateTransitionError
from auditor.shared.domain.vocabulary import JobKind


class RetryProcessing:
    """FAILED → resumes from the last successful step: extraction if any document is pending,
    otherwise analysis (which itself skips criteria that already have a finding)."""

    def __init__(
        self,
        access: EvaluationAccess,
        lifecycle: EvaluationLifecycle,
        documents: DocumentRepository,
        jobs: JobRepository,
        runner: JobRunner,
        uow: UnitOfWork,
        max_attempts: int,
    ) -> None:
        self._access = access
        self._lifecycle = lifecycle
        self._documents = documents
        self._jobs = jobs
        self._runner = runner
        self._uow = uow
        self._max_attempts = max_attempts

    async def execute(self, actor: Actor, evaluation_id: UUID) -> Evaluation:
        evaluation = await self._access.require(actor, evaluation_id, Permission.RETRY_PROCESSING)
        if evaluation.status is not EvaluationStatus.FAILED:
            raise InvalidStateTransitionError("Solo se pueden reintentar evaluaciones con error.")
        run = await self._lifecycle.current_run(evaluation)
        extracted = await self._documents.all_extracted(run.id)
        trigger, kind = (
            (Trigger.RETRY_ANALYSIS, JobKind.ANALYSIS)
            if extracted
            else (Trigger.RETRY_EXTRACTION, JobKind.EXTRACTION)
        )
        updated = await self._lifecycle.transition(
            evaluation, trigger, Party.REVIEWER, actor_id=actor.user_id, actor_role=actor.role
        )
        job = await self._jobs.enqueue(
            evaluation.id, run.id, kind, self._max_attempts, actor.user_id
        )
        await self._uow.commit()
        self._runner.submit(job.id)
        return updated
