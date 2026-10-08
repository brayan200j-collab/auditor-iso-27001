from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from auditor.review.domain.results import PlanPhase, coverage, gaps, improvement_plan
from auditor.review.domain.review import FinalFinding, FinalValues
from auditor.shared.domain.vocabulary import FindingStatus, Level, Priority, ReviewStatus


def _final(
    code: str,
    status: FindingStatus | None,
    priority: Priority | None = Priority.MEDIUM,
    risk: Level | None = Level.MEDIUM,
    effort: Level | None = Level.MEDIUM,
    review: ReviewStatus = ReviewStatus.APPROVED,
) -> FinalFinding:
    return FinalFinding(
        id=uuid4(),
        ai_finding_id=uuid4(),
        evaluation_id=uuid4(),
        analysis_run_id=uuid4(),
        checklist_item_id=uuid4(),
        criterion_code=code,
        review_status=review,
        values=FinalValues(status, "brecha", "recomendación", priority, effort, risk),
        evidence=(),
        reviewer_comment=None,
        reviewed_by=uuid4(),
        reviewed_at=datetime.now(UTC),
    )


FINALS = [
    _final("ISO-01", FindingStatus.FOUND),
    _final("ISO-02", FindingStatus.PARTIAL, Priority.LOW),
    _final("ISO-03", FindingStatus.NO_DOCUMENTARY_EVIDENCE, Priority.CRITICAL, Level.LOW),
    _final("ISO-04", FindingStatus.PARTIAL, Priority.CRITICAL, Level.HIGH, Level.HIGH),
    _final("ISO-05", FindingStatus.PARTIAL, Priority.CRITICAL, Level.HIGH, Level.LOW),
    _final("ISO-06", None, None, None, None, ReviewStatus.DISCARDED),
    _final("ISO-07", FindingStatus.NO_DOCUMENTARY_EVIDENCE, Priority.MEDIUM),
]


def test_coverage_is_counts_and_excludes_discarded() -> None:
    result = coverage(FINALS, 30)
    assert (result.total, result.found, result.partial, result.no_evidence, result.discarded) == (
        30,
        1,
        3,
        2,
        1,
    )


def test_gaps_are_ordered_by_priority_then_risk_then_effort() -> None:
    assert [g.criterion_code for g in gaps(FINALS)] == [
        "ISO-05",
        "ISO-04",
        "ISO-03",
        "ISO-07",
        "ISO-02",
    ]


def test_plan_groups_gaps_into_phases_by_priority() -> None:
    plan = improvement_plan(FINALS)
    assert list(plan) == [PlanPhase.FIRST, PlanPhase.NEXT, PlanPhase.LATER]
    assert [f.criterion_code for f in plan[PlanPhase.FIRST]] == ["ISO-05", "ISO-04", "ISO-03"]
    assert [f.criterion_code for f in plan[PlanPhase.LATER]] == ["ISO-02"]


def test_empty_plan_when_everything_has_evidence() -> None:
    assert improvement_plan([_final("ISO-01", FindingStatus.FOUND)]) == {}
