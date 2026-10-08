from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from auditor.metrics.application.get_dashboard import GetDashboard
from auditor.metrics.application.get_pilot_metrics import GetPilotMetrics
from auditor.shared.api.dependencies import CurrentActor, use_case
from auditor.shared.api.schemas import ERROR_RESPONSES, ApiModel

router = APIRouter(prefix="/api/v1", tags=["metrics"], responses=ERROR_RESPONSES)


class DashboardResponse(ApiModel):
    active_evaluations: int
    pending_review: int
    approved: int
    documents_processed: int
    high_priority_findings: int


class TechnicalMetricsResponse(ApiModel):
    documents_attempted: int
    documents_processed_ok: int
    processed_ok_ratio: float | None
    extraction_errors: int
    processing_failures: int
    average_analysis_seconds: int | None
    llm_calls: int
    approximate_tokens: int
    findings_reviewed: int
    findings_modified: int
    authorization_denials: int


class ValueMetricsResponse(ApiModel):
    responses: int
    average_manual_hours: float | None
    average_system_hours: float | None
    average_usefulness: float | None
    average_ease_of_use: float | None
    average_trust: float | None
    actionable_yes: int
    average_willingness_to_use: float | None
    pay_yes: int
    pay_maybe: int
    pay_no: int


class MetricsResponse(ApiModel):
    anonymized: bool
    technical: TechnicalMetricsResponse
    value: ValueMetricsResponse


def _number(value: object) -> float | None:
    return None if value is None else float(str(value))


@router.get("/dashboard", response_model=DashboardResponse, summary="Resumen del panel")
async def dashboard(
    actor: CurrentActor,
    get: Annotated[GetDashboard, Depends(use_case(GetDashboard))],
) -> DashboardResponse:
    counts = await get.execute(actor)
    return DashboardResponse(
        active_evaluations=counts.active_evaluations,
        pending_review=counts.pending_review,
        approved=counts.approved,
        documents_processed=counts.documents_processed,
        high_priority_findings=counts.high_priority_findings,
    )


@router.get("/metrics", response_model=MetricsResponse, summary="Métricas del piloto")
async def metrics(
    actor: CurrentActor,
    get: Annotated[GetPilotMetrics, Depends(use_case(GetPilotMetrics))],
) -> MetricsResponse:
    result = await get.execute(actor)
    t, v = result.technical, result.value
    return MetricsResponse(
        anonymized=result.anonymized,
        technical=TechnicalMetricsResponse(
            documents_attempted=t.documents_attempted,
            documents_processed_ok=t.documents_processed_ok,
            processed_ok_ratio=_number(t.processed_ok_ratio),
            extraction_errors=t.extraction_errors,
            processing_failures=t.processing_failures,
            average_analysis_seconds=t.average_analysis_seconds,
            llm_calls=t.llm_calls,
            approximate_tokens=t.approximate_tokens,
            findings_reviewed=t.findings_reviewed,
            findings_modified=t.findings_modified,
            authorization_denials=t.authorization_denials,
        ),
        value=ValueMetricsResponse(
            responses=v.responses,
            average_manual_hours=_number(v.average_manual_hours),
            average_system_hours=_number(v.average_system_hours),
            average_usefulness=_number(v.average_usefulness),
            average_ease_of_use=_number(v.average_ease_of_use),
            average_trust=_number(v.average_trust),
            actionable_yes=v.actionable_yes,
            average_willingness_to_use=_number(v.average_willingness_to_use),
            pay_yes=v.pay_yes,
            pay_maybe=v.pay_maybe,
            pay_no=v.pay_no,
        ),
    )
