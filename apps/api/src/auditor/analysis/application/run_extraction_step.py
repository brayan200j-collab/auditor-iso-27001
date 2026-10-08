from __future__ import annotations

from auditor.documents.public import ExtractRunDocuments
from auditor.evaluations.public import EvaluationLifecycle, EvaluationStatus, Party, Trigger
from auditor.shared.application.jobs import JobRecord, JobRepository, JobRunner
from auditor.shared.application.ports import UnitOfWork
from auditor.shared.domain.vocabulary import JobKind


class RunExtractionStep:
    """Background step: extract and chunk the run's documents, then queue the analysis.

    Idempotent: if the evaluation already moved past EXTRACTING the job does nothing.
    """

    def __init__(
        self,
        lifecycle: EvaluationLifecycle,
        extraction: ExtractRunDocuments,
        jobs: JobRepository,
        runner: JobRunner,
        uow: UnitOfWork,
        max_attempts: int,
    ) -> None:
        self._lifecycle = lifecycle
        self._extraction = extraction
        self._jobs = jobs
        self._runner = runner
        self._uow = uow
        self._max_attempts = max_attempts

    async def execute(self, job: JobRecord) -> None:
        evaluation = await self._lifecycle.load_for_system(job.evaluation_id)
        if evaluation is None or evaluation.status is not EvaluationStatus.EXTRACTING:
            return
        summary = await self._extraction.execute(job.analysis_run_id, evaluation.company_id)
        await self._lifecycle.transition(
            evaluation,
            Trigger.EXTRACTION_COMPLETED,
            Party.SYSTEM,
            details={
                "documents": summary.documents,
                "pages": summary.pages,
                "chunks": summary.chunks,
            },
        )
        next_job = await self._jobs.enqueue(
            evaluation.id, job.analysis_run_id, JobKind.ANALYSIS, self._max_attempts, None
        )
        await self._uow.commit()
        self._runner.submit(next_job.id)
