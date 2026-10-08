from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.reports.domain.report import Report
from auditor.reports.infrastructure.models import ReportModel


def _to_report(model: ReportModel) -> Report:
    return Report(
        id=model.id,
        evaluation_id=model.evaluation_id,
        company_id=model.company_id,
        analysis_run_id=model.analysis_run_id,
        version=model.version,
        storage_path=model.storage_path,
        size_bytes=model.size_bytes,
        sha256=model.sha256,
        generated_at=model.generated_at,
    )


class SqlReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, report_id: UUID) -> Report | None:
        model = await self._session.get(ReportModel, report_id)
        return _to_report(model) if model else None

    async def latest_for_evaluation(self, evaluation_id: UUID) -> Report | None:
        model = await self._session.scalar(
            select(ReportModel)
            .where(ReportModel.evaluation_id == evaluation_id)
            .order_by(ReportModel.version.desc())
            .limit(1)
        )
        return _to_report(model) if model else None

    async def for_run(self, analysis_run_id: UUID) -> Report | None:
        model = await self._session.scalar(
            select(ReportModel)
            .where(ReportModel.analysis_run_id == analysis_run_id)
            .order_by(ReportModel.version.desc())
            .limit(1)
        )
        return _to_report(model) if model else None

    async def next_version(self, evaluation_id: UUID) -> int:
        current = await self._session.scalar(
            select(func.max(ReportModel.version)).where(ReportModel.evaluation_id == evaluation_id)
        )
        return (current or 0) + 1

    async def add(self, report: Report, generated_by: UUID | None) -> None:
        self._session.add(
            ReportModel(
                id=report.id,
                evaluation_id=report.evaluation_id,
                company_id=report.company_id,
                analysis_run_id=report.analysis_run_id,
                version=report.version,
                storage_path=report.storage_path,
                size_bytes=report.size_bytes,
                sha256=report.sha256,
                generated_by=generated_by,
                generated_at=report.generated_at,
            )
        )
        await self._session.flush()
