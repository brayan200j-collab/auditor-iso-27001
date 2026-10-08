from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from auditor.evaluations.public import EvaluationAccess, EvaluationStatus
from auditor.identity.public import Permission
from auditor.reports.application.ports import ReportRepository
from auditor.reports.domain.report import Report, ReportState
from auditor.shared.application.jobs import JobRepository
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.vocabulary import JobKind, JobStatus


@dataclass(frozen=True, slots=True)
class ReportStatus:
    state: ReportState
    report: Report | None


class GetReportStatus:
    def __init__(
        self, access: EvaluationAccess, reports: ReportRepository, jobs: JobRepository
    ) -> None:
        self._access = access
        self._reports = reports
        self._jobs = jobs

    async def execute(self, actor: Actor, evaluation_id: UUID) -> ReportStatus:
        evaluation = await self._access.require(
            actor, evaluation_id, Permission.VIEW_APPROVED_RESULTS
        )
        if evaluation.status is not EvaluationStatus.APPROVED:
            return ReportStatus(ReportState.NONE, None)
        job = await self._jobs.latest_for(evaluation.id, JobKind.REPORT)
        report = await self._reports.latest_for_evaluation(evaluation.id)
        if job and job.status in {JobStatus.QUEUED, JobStatus.RUNNING}:
            return ReportStatus(ReportState.PENDING, report)
        if report:
            return ReportStatus(ReportState.READY, report)
        if job and job.status is JobStatus.FAILED:
            return ReportStatus(ReportState.FAILED, None)
        return ReportStatus(ReportState.NONE, None)
