from __future__ import annotations

from decimal import Decimal

from auditor.metrics.domain.metrics import (
    SurveyTotals,
    TechnicalTotals,
    technical_metrics,
    value_metrics,
)

EMPTY_TECH = TechnicalTotals(0, 0, 0, 0, 0, 0.0, 0, 0, 0, 0, 0)
EMPTY_SURVEY = SurveyTotals(0, Decimal(0), Decimal(0), 0, 0, 0, 0, 0, 0, 0, 0)


def test_without_data_nothing_is_invented() -> None:
    tech = technical_metrics(EMPTY_TECH)
    assert tech.processed_ok_ratio is None
    assert tech.average_analysis_seconds is None
    value = value_metrics(EMPTY_SURVEY)
    assert value.responses == 0
    assert value.average_manual_hours is None
    assert value.average_usefulness is None


def test_technical_ratios_and_averages() -> None:
    tech = technical_metrics(
        TechnicalTotals(
            documents_uploaded=9,
            documents_extracted=8,
            documents_rejected=1,
            processing_failures=1,
            analysis_runs_finished=2,
            analysis_seconds_total=181.0,
            llm_calls=40,
            tokens=60_000,
            findings_reviewed=60,
            findings_modified=7,
            authorization_denials=3,
        )
    )
    assert tech.documents_attempted == 10
    assert tech.processed_ok_ratio == Decimal("0.800")
    assert tech.average_analysis_seconds == 90
    assert (tech.extraction_errors, tech.findings_modified) == (1, 7)


def test_survey_averages_are_rounded_to_one_decimal() -> None:
    value = value_metrics(
        SurveyTotals(
            responses=3,
            manual_hours_sum=Decimal("40.0"),
            system_hours_sum=Decimal("4.5"),
            usefulness_sum=13,
            ease_sum=12,
            trust_sum=11,
            actionable_yes=2,
            willingness_to_use_sum=14,
            pay_yes=1,
            pay_maybe=1,
            pay_no=1,
        )
    )
    assert value.average_manual_hours == Decimal("13.3")
    assert value.average_system_hours == Decimal("1.5")
    assert value.average_usefulness == Decimal("4.3")
    assert value.average_trust == Decimal("3.7")
    assert (value.pay_yes, value.pay_maybe, value.pay_no) == (1, 1, 1)
