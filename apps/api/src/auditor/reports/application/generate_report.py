from __future__ import annotations

import hashlib
from uuid import uuid4

from auditor.documents.public import DocumentRepository
from auditor.evaluations.public import EvaluationLifecycle, EvaluationStatus, NameDirectory
from auditor.reports.application.ports import (
    AnalysedDocument,
    ReportContent,
    ReportRenderer,
    ReportRepository,
)
from auditor.reports.domain.report import Report, report_path
from auditor.review.public import GetApprovedResults
from auditor.shared.application.jobs import JobRecord, PermanentJobError
from auditor.shared.application.ports import AuditLogger, Clock, ObjectStorage, UnitOfWork
from auditor.shared.domain.audit import AuditAction, AuditEntry


class GenerateReport:
    """REPORT job: renders the reviewed results to PDF and stores it privately.

    Idempotent per analysis run: when a report already exists for the run, nothing is redone.
    """

    def __init__(
        self,
        lifecycle: EvaluationLifecycle,
        results: GetApprovedResults,
        documents: DocumentRepository,
        companies: NameDirectory,
        users: NameDirectory,
        reports: ReportRepository,
        renderer: ReportRenderer,
        storage: ObjectStorage,
        audit: AuditLogger,
        uow: UnitOfWork,
        clock: Clock,
        bucket: str,
    ) -> None:
        self._lifecycle = lifecycle
        self._results = results
        self._documents = documents
        self._companies = companies
        self._users = users
        self._reports = reports
        self._renderer = renderer
        self._storage = storage
        self._audit = audit
        self._uow = uow
        self._clock = clock
        self._bucket = bucket

    async def execute(self, job: JobRecord) -> None:
        evaluation = await self._lifecycle.load_for_system(job.evaluation_id)
        if evaluation is None or evaluation.status is not EvaluationStatus.APPROVED:
            raise PermanentJobError("report requested for an evaluation that is not approved")
        if await self._reports.for_run(job.analysis_run_id):
            return

        results = await self._results.for_evaluation(evaluation)
        run = await self._lifecycle.current_run(evaluation)
        documents = await self._documents.list_for_run(run.id, evaluation.company_id)
        companies = await self._companies.names_of([evaluation.company_id])
        reviewer = evaluation.approved_by or evaluation.reviewer_id
        reviewers = await self._users.names_of([reviewer]) if reviewer else {}
        now = self._clock.now()
        pdf = await self._renderer.render(
            ReportContent(
                company_name=companies.get(evaluation.company_id, "—"),
                reviewer_name=reviewers.get(reviewer) if reviewer else None,
                generated_at=now,
                documents=[AnalysedDocument(d.original_name, d.page_count) for d in documents],
                results=results,
            )
        )

        report_id = uuid4()
        path = report_path(evaluation.company_id, evaluation.id, report_id)
        await self._storage.upload(self._bucket, path, pdf, "application/pdf")
        report = Report(
            id=report_id,
            evaluation_id=evaluation.id,
            company_id=evaluation.company_id,
            analysis_run_id=run.id,
            version=await self._reports.next_version(evaluation.id),
            storage_path=path,
            size_bytes=len(pdf),
            sha256=hashlib.sha256(pdf).hexdigest(),
            generated_at=now,
        )
        await self._reports.add(report, generated_by=None)
        await self._audit.record(
            AuditEntry(
                action=AuditAction.REPORT_GENERATED,
                company_id=evaluation.company_id,
                resource_type="report",
                resource_id=report.id,
                details={"evaluation_id": str(evaluation.id), "version": report.version},
            )
        )
        await self._uow.commit()
