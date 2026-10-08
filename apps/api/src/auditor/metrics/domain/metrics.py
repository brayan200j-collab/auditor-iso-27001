"""Role dashboards and pilot metrics (CLAUDE.md sections 18 and 19).

Every value is computed from recorded data. Without data the value is None and the UI shows
"Sin datos aún"; nothing is ever estimated or invented. Metrics are aggregates only: they never
carry company names, users or document content.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


@dataclass(frozen=True, slots=True)
class DashboardCounts:
    active_evaluations: int
    pending_review: int
    approved: int
    documents_processed: int
    high_priority_findings: int


@dataclass(frozen=True, slots=True)
class TechnicalTotals:
    documents_uploaded: int
    documents_extracted: int
    documents_rejected: int
    processing_failures: int
    analysis_runs_finished: int
    analysis_seconds_total: float
    llm_calls: int
    tokens: int
    findings_reviewed: int
    findings_modified: int
    authorization_denials: int


@dataclass(frozen=True, slots=True)
class SurveyTotals:
    responses: int
    manual_hours_sum: Decimal
    system_hours_sum: Decimal
    usefulness_sum: int
    ease_sum: int
    trust_sum: int
    actionable_yes: int
    willingness_to_use_sum: int
    pay_yes: int
    pay_maybe: int
    pay_no: int


@dataclass(frozen=True, slots=True)
class TechnicalMetrics:
    documents_attempted: int
    documents_processed_ok: int
    processed_ok_ratio: Decimal | None
    extraction_errors: int
    processing_failures: int
    average_analysis_seconds: int | None
    llm_calls: int
    approximate_tokens: int
    findings_reviewed: int
    findings_modified: int
    authorization_denials: int


@dataclass(frozen=True, slots=True)
class ValueMetrics:
    responses: int
    average_manual_hours: Decimal | None
    average_system_hours: Decimal | None
    average_usefulness: Decimal | None
    average_ease_of_use: Decimal | None
    average_trust: Decimal | None
    actionable_yes: int
    average_willingness_to_use: Decimal | None
    pay_yes: int
    pay_maybe: int
    pay_no: int


@dataclass(frozen=True, slots=True)
class PilotMetrics:
    technical: TechnicalMetrics
    value: ValueMetrics
    anonymized: bool


_ONE_DECIMAL = Decimal("0.1")


def _average(total: Decimal | int, count: int) -> Decimal | None:
    if count == 0:
        return None
    return (Decimal(total) / count).quantize(_ONE_DECIMAL, rounding=ROUND_HALF_UP)


def technical_metrics(totals: TechnicalTotals) -> TechnicalMetrics:
    attempted = totals.documents_uploaded + totals.documents_rejected
    ratio = (
        (Decimal(totals.documents_extracted) / attempted).quantize(Decimal("0.001"))
        if attempted
        else None
    )
    average_seconds = (
        round(totals.analysis_seconds_total / totals.analysis_runs_finished)
        if totals.analysis_runs_finished
        else None
    )
    return TechnicalMetrics(
        documents_attempted=attempted,
        documents_processed_ok=totals.documents_extracted,
        processed_ok_ratio=ratio,
        extraction_errors=totals.documents_rejected,
        processing_failures=totals.processing_failures,
        average_analysis_seconds=average_seconds,
        llm_calls=totals.llm_calls,
        approximate_tokens=totals.tokens,
        findings_reviewed=totals.findings_reviewed,
        findings_modified=totals.findings_modified,
        authorization_denials=totals.authorization_denials,
    )


def value_metrics(totals: SurveyTotals) -> ValueMetrics:
    n = totals.responses
    return ValueMetrics(
        responses=n,
        average_manual_hours=_average(totals.manual_hours_sum, n),
        average_system_hours=_average(totals.system_hours_sum, n),
        average_usefulness=_average(totals.usefulness_sum, n),
        average_ease_of_use=_average(totals.ease_sum, n),
        average_trust=_average(totals.trust_sum, n),
        actionable_yes=totals.actionable_yes,
        average_willingness_to_use=_average(totals.willingness_to_use_sum, n),
        pay_yes=totals.pay_yes,
        pay_maybe=totals.pay_maybe,
        pay_no=totals.pay_no,
    )
