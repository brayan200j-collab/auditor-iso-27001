from __future__ import annotations

from uuid import UUID

from auditor.evaluations.public import Evaluation, EvaluationLifecycle
from auditor.shared.application.jobs import JobRecord, JobRepository, JobRunner
from auditor.shared.application.ports import UnitOfWork
from auditor.shared.domain.vocabulary import JobKind


class ScheduleReport:
    """Queues the REPORT step of an approved evaluation (idempotent while a job is active)."""

    def __init__(
        self,
        lifecycle: EvaluationLifecycle,
        jobs: JobRepository,
        runner: JobRunner,
        uow: UnitOfWork,
        max_attempts: int,
    ) -> None:
        self._lifecycle = lifecycle
        self._jobs = jobs
        self._runner = runner
        self._uow = uow
        self._max_attempts = max_attempts

    async def execute(self, evaluation: Evaluation, requested_by: UUID | None) -> JobRecord:
        run = await self._lifecycle.current_run(evaluation)
        job = await self._jobs.enqueue(
            evaluation.id, run.id, JobKind.REPORT, self._max_attempts, requested_by
        )
        await self._uow.commit()
        self._runner.submit(job.id)
        return job
