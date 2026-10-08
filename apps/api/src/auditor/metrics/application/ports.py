from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from auditor.metrics.domain.metrics import DashboardCounts, SurveyTotals, TechnicalTotals


@dataclass(frozen=True, slots=True)
class DashboardScope:
    """Which evaluations count: a company's (SME), assigned ones (reviewer) or all (admin)."""

    company_id: UUID | None = None
    reviewer_id: UUID | None = None


class MetricsReader(Protocol):
    async def dashboard(self, scope: DashboardScope) -> DashboardCounts: ...

    async def technical_totals(self) -> TechnicalTotals: ...

    async def survey_totals(self) -> SurveyTotals: ...
