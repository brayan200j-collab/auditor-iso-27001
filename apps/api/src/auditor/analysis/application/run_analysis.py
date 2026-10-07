"""Background analysis step: every active criterion of the run's checklist gets one AI finding.

Resumable (CLAUDE.md section 10): criteria that already have a finding are skipped, so a retry or
a recovered job continues where it stopped and never duplicates findings.
"""

from __future__ import annotations

import asyncio
from collections import Counter
from collections.abc import Awaitable, Callable

from auditor.analysis.application.evaluate_criterion import CriterionEvaluator, CriterionTask
from auditor.analysis.application.ports import FindingRepository
from auditor.checklist.public import ChecklistRepository
from auditor.evaluations.public import EvaluationLifecycle, EvaluationStatus, Party, Trigger
from auditor.shared.application.jobs import JobRecord, PermanentJobError
from auditor.shared.application.ports import AuditLogger, UnitOfWork
from auditor.shared.domain.audit import AuditAction, AuditEntry
from auditor.shared.domain.errors import QuotaExceededError

QUOTA_EXCEEDED = "QUOTA_EXCEEDED"


class PlanAnalysis:
    def __init__(
        self,
        lifecycle: EvaluationLifecycle,
        checklists: ChecklistRepository,
        findings: FindingRepository,
    ) -> None:
        self._lifecycle = lifecycle
        self._checklists = checklists
        self._findings = findings

    async def execute(self, job: JobRecord) -> list[CriterionTask] | None:
        """Pending criteria, or None if the evaluation is no longer being analysed."""
        evaluation = await self._lifecycle.load_for_system(job.evaluation_id)
        if evaluation is None or evaluation.status is not EvaluationStatus.ANALYZING:
            return None
        run = await self._lifecycle.get_run(job.analysis_run_id)
        if run is None or run.checklist_version_id is None:
            raise PermanentJobError("ANALYSIS_ERROR", "run without checklist version")
        version = await self._checklists.get(run.checklist_version_id)
        if version is None:
            raise PermanentJobError("ANALYSIS_ERROR", "checklist version not found")
        done = await self._findings.evaluated_item_ids(run.id)
        return [
            CriterionTask(evaluation.id, run.id, item)
            for item in version.active_items
            if item.id not in done
        ]


class EvaluateAndStore:
    """Evaluates one criterion and stores its finding in its own transaction."""

    def __init__(
        self, evaluator: CriterionEvaluator, findings: FindingRepository, uow: UnitOfWork
    ) -> None:
        self._evaluator = evaluator
        self._findings = findings
        self._uow = uow

    async def execute(self, task: CriterionTask) -> None:
        if task.item.id in await self._findings.evaluated_item_ids(task.analysis_run_id):
            return
        await self._findings.add(await self._evaluator.evaluate(task))
        await self._uow.commit()


class CompleteAnalysis:
    def __init__(
        self,
        lifecycle: EvaluationLifecycle,
        checklists: ChecklistRepository,
        findings: FindingRepository,
        audit: AuditLogger,
        uow: UnitOfWork,
    ) -> None:
        self._lifecycle = lifecycle
        self._checklists = checklists
        self._findings = findings
        self._audit = audit
        self._uow = uow

    async def execute(self, job: JobRecord) -> None:
        evaluation = await self._lifecycle.load_for_system(job.evaluation_id)
        if evaluation is None or evaluation.status is not EvaluationStatus.ANALYZING:
            return
        findings = await self._findings.list_for_run(job.analysis_run_id)
        statuses = Counter(
            (finding.status.value if finding.status else "ERROR") for finding in findings
        )
        await self._lifecycle.transition(
            evaluation, Trigger.ANALYSIS_COMPLETED, Party.SYSTEM, details=dict(statuses)
        )
        run = await self._lifecycle.get_run(job.analysis_run_id)
        if run is not None:
            await self._lifecycle.mark_run_finished(run)
        await self._audit.record(
            AuditEntry(
                action=AuditAction.FINDINGS_GENERATED,
                actor_role=Party.SYSTEM.value,
                company_id=evaluation.company_id,
                resource_type="evaluation",
                resource_id=evaluation.id,
                details={"findings": len(findings), **dict(statuses)},
            )
        )
        await self._uow.commit()


Plan = Callable[[JobRecord], Awaitable[list[CriterionTask] | None]]
EvaluateOne = Callable[[CriterionTask], Awaitable[None]]
Complete = Callable[[JobRecord], Awaitable[None]]


class AnalysisOrchestrator:
    """Runs pending criteria with bounded concurrency; each one uses its own unit of work."""

    def __init__(self, plan: Plan, evaluate_one: EvaluateOne, complete: Complete, concurrency: int):
        self._plan = plan
        self._evaluate_one = evaluate_one
        self._complete = complete
        self._semaphore = asyncio.Semaphore(concurrency)

    async def run(self, job: JobRecord) -> None:
        tasks = await self._plan(job)
        if tasks is None:
            return

        async def bounded(task: CriterionTask) -> None:
            async with self._semaphore:
                await self._evaluate_one(task)

        results = await asyncio.gather(*(bounded(task) for task in tasks), return_exceptions=True)
        errors = [result for result in results if isinstance(result, BaseException)]
        if any(isinstance(error, QuotaExceededError) for error in errors):
            raise PermanentJobError(QUOTA_EXCEEDED)
        if errors:
            raise errors[0]
        await self._complete(job)
