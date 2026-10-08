"""Read model for dashboards and pilot metrics.

Aggregates span several modules, so they are read with plain SQL over the tables instead of
importing other modules' internals. Only counts and sums leave this class.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.metrics.application.ports import DashboardScope
from auditor.metrics.domain.metrics import DashboardCounts, SurveyTotals, TechnicalTotals

_DASHBOARD = text(
    """
    WITH scoped AS (
        SELECT e.id, e.status FROM evaluations e
        WHERE (CAST(:company_id AS uuid) IS NULL OR e.company_id = CAST(:company_id AS uuid))
          AND (CAST(:reviewer_id AS uuid) IS NULL OR e.reviewer_id = CAST(:reviewer_id AS uuid))
    )
    SELECT
        (SELECT count(*) FROM scoped
          WHERE status IN ('DRAFT', 'RECEIVED', 'EXTRACTING', 'ANALYZING', 'PENDING_REVIEW',
                           'FAILED')) AS active,
        (SELECT count(*) FROM scoped WHERE status = 'PENDING_REVIEW') AS pending_review,
        (SELECT count(*) FROM scoped WHERE status = 'APPROVED') AS approved,
        (SELECT count(*) FROM documents d JOIN scoped s ON s.id = d.evaluation_id
          WHERE d.extracted_at IS NOT NULL) AS documents_processed,
        (SELECT count(*) FROM final_findings f JOIN scoped s ON s.id = f.evaluation_id
          WHERE s.status = 'APPROVED' AND f.review_status <> 'DISCARDED'
            AND f.status <> 'FOUND' AND f.priority IN ('CRITICAL', 'HIGH')) AS high_priority
    """
)

_TECHNICAL = text(
    """
    SELECT
        (SELECT count(*) FROM documents) AS uploaded,
        (SELECT count(*) FROM documents WHERE extracted_at IS NOT NULL) AS extracted,
        (SELECT count(*) FROM audit_logs WHERE action = 'DOCUMENT_REJECTED') AS rejected,
        (SELECT count(*) FROM audit_logs WHERE action = 'PROCESSING_FAILED') AS failures,
        (SELECT count(*) FROM analysis_runs
          WHERE started_at IS NOT NULL AND finished_at IS NOT NULL) AS runs,
        (SELECT coalesce(sum(extract(epoch FROM finished_at - started_at)), 0)
           FROM analysis_runs
          WHERE started_at IS NOT NULL AND finished_at IS NOT NULL) AS seconds,
        (SELECT count(*) FROM llm_calls) AS llm_calls,
        (SELECT coalesce(sum(coalesce(input_tokens, 0) + coalesce(output_tokens, 0)), 0)
           FROM llm_calls) AS tokens,
        (SELECT count(*) FROM final_findings) AS reviewed,
        (SELECT count(*) FROM final_findings
          WHERE review_status IN ('EDITED_APPROVED', 'DISCARDED')) AS modified,
        (SELECT count(*) FROM audit_logs WHERE action = 'ACCESS_DENIED') AS denials
    """
)

_SURVEY = text(
    """
    SELECT
        count(*) AS responses,
        coalesce(sum(manual_time_hours), 0) AS manual,
        coalesce(sum(system_time_hours), 0) AS system,
        coalesce(sum(usefulness), 0) AS usefulness,
        coalesce(sum(ease_of_use), 0) AS ease,
        coalesce(sum(trust_in_results), 0) AS trust,
        count(*) FILTER (WHERE actionable_recommendations) AS actionable,
        coalesce(sum(willingness_to_use), 0) AS willing,
        count(*) FILTER (WHERE willingness_to_pay = 'YES') AS pay_yes,
        count(*) FILTER (WHERE willingness_to_pay = 'MAYBE') AS pay_maybe,
        count(*) FILTER (WHERE willingness_to_pay = 'NO') AS pay_no
    FROM feedback
    """
)


class SqlMetricsReader:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _row(self, query: Any, **params: Any) -> Any:
        return (await self._session.execute(query, params)).one()

    async def dashboard(self, scope: DashboardScope) -> DashboardCounts:
        row = await self._row(
            _DASHBOARD,
            company_id=str(scope.company_id) if scope.company_id else None,
            reviewer_id=str(scope.reviewer_id) if scope.reviewer_id else None,
        )
        return DashboardCounts(
            active_evaluations=row.active,
            pending_review=row.pending_review,
            approved=row.approved,
            documents_processed=row.documents_processed,
            high_priority_findings=row.high_priority,
        )

    async def technical_totals(self) -> TechnicalTotals:
        row = await self._row(_TECHNICAL)
        return TechnicalTotals(
            documents_uploaded=row.uploaded,
            documents_extracted=row.extracted,
            documents_rejected=row.rejected,
            processing_failures=row.failures,
            analysis_runs_finished=row.runs,
            analysis_seconds_total=float(row.seconds),
            llm_calls=row.llm_calls,
            tokens=int(row.tokens),
            findings_reviewed=row.reviewed,
            findings_modified=row.modified,
            authorization_denials=row.denials,
        )

    async def survey_totals(self) -> SurveyTotals:
        row = await self._row(_SURVEY)
        return SurveyTotals(
            responses=row.responses,
            manual_hours_sum=Decimal(row.manual),
            system_hours_sum=Decimal(row.system),
            usefulness_sum=int(row.usefulness),
            ease_sum=int(row.ease),
            trust_sum=int(row.trust),
            actionable_yes=row.actionable,
            willingness_to_use_sum=int(row.willing),
            pay_yes=row.pay_yes,
            pay_maybe=row.pay_maybe,
            pay_no=row.pay_no,
        )
