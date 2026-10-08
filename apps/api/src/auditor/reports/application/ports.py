from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from auditor.reports.domain.report import Report
from auditor.review.public import ResultsView


class ReportRepository(Protocol):
    async def get(self, report_id: UUID) -> Report | None: ...

    async def latest_for_evaluation(self, evaluation_id: UUID) -> Report | None: ...

    async def for_run(self, analysis_run_id: UUID) -> Report | None: ...

    async def next_version(self, evaluation_id: UUID) -> int: ...

    async def add(self, report: Report, generated_by: UUID | None) -> None: ...


@dataclass(frozen=True, slots=True)
class AnalysedDocument:
    name: str
    pages: int


@dataclass(frozen=True, slots=True)
class ReportContent:
    """Everything the template needs; only reviewed results, never raw AI output."""

    company_name: str
    reviewer_name: str | None
    generated_at: datetime
    documents: list[AnalysedDocument]
    results: ResultsView


class ReportRenderer(Protocol):
    async def render(self, content: ReportContent) -> bytes: ...
