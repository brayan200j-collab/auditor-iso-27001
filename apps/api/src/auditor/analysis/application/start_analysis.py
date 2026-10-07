from __future__ import annotations

from uuid import UUID

from auditor.checklist.public import ChecklistRepository
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
from auditor.shared.domain.errors import (
    ConflictError,
    InvalidStateTransitionError,
    ValidationFailedError,
)
from auditor.shared.domain.vocabulary import JobKind


class StartAnalysis:
    """RECEIVED → EXTRACTING: binds the published checklist and queues the extraction job."""

    def __init__(
        self,
        access: EvaluationAccess,
        lifecycle: EvaluationLifecycle,
        documents: DocumentRepository,
        checklists: ChecklistRepository,
        jobs: JobRepository,
        runner: JobRunner,
        uow: UnitOfWork,
        max_attempts: int,
    ) -> None:
        self._access = access
        self._lifecycle = lifecycle
        self._documents = documents
        self._checklists = checklists
        self._jobs = jobs
        self._runner = runner
        self._uow = uow
        self._max_attempts = max_attempts

    async def execute(self, actor: Actor, evaluation_id: UUID) -> Evaluation:
        evaluation = await self._access.require(actor, evaluation_id, Permission.UPLOAD_DOCUMENTS)
        if evaluation.status is not EvaluationStatus.RECEIVED:
            raise InvalidStateTransitionError(
                "Carga al menos un documento antes de iniciar el análisis."
            )
        run = await self._lifecycle.current_run(evaluation)
        if await self._documents.count_for_run(run.id) == 0:
            raise ValidationFailedError("Carga al menos un documento antes de iniciar el análisis.")
        checklist = await self._checklists.latest_published()
        if checklist is None:
            raise ConflictError("No hay un checklist publicado. Contacta al administrador.")

        updated = await self._lifecycle.transition(
            evaluation,
            Trigger.START_ANALYSIS,
            Party.SME,
            actor_id=actor.user_id,
            actor_role=actor.role,
            details={"checklist_version": checklist.version},
        )
        await self._lifecycle.bind_checklist(run, checklist.id)
        await self._lifecycle.mark_run_started(run)
        job = await self._jobs.enqueue(
            evaluation.id, run.id, JobKind.EXTRACTION, self._max_attempts, actor.user_id
        )
        await self._uow.commit()
        self._runner.submit(job.id)
        return updated
