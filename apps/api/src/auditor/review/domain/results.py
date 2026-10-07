"""Approved results for the company (CLAUDE.md section 15).

Coverage is expressed only as counts, never as a percentage. Gaps are the reviewed findings that
are partial or without documentary evidence, ordered by priority, risk and effort; the initial
improvement plan groups them into three phases by priority.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import IntEnum

from auditor.review.domain.review import FinalFinding
from auditor.shared.domain.gap_ordering import order_gaps
from auditor.shared.domain.vocabulary import FindingStatus, Priority, ReviewStatus


@dataclass(frozen=True, slots=True)
class Coverage:
    total: int
    found: int
    partial: int
    no_evidence: int
    discarded: int


class PlanPhase(IntEnum):
    """1 = address first (critical/high), 2 = next (medium), 3 = later (low)."""

    FIRST = 1
    NEXT = 2
    LATER = 3


_PHASE_BY_PRIORITY = {
    Priority.CRITICAL: PlanPhase.FIRST,
    Priority.HIGH: PlanPhase.FIRST,
    Priority.MEDIUM: PlanPhase.NEXT,
    Priority.LOW: PlanPhase.LATER,
}


def visible(finals: Sequence[FinalFinding]) -> list[FinalFinding]:
    """Discarded findings never reach the company."""
    return [f for f in finals if f.review_status is not ReviewStatus.DISCARDED]


def coverage(finals: Sequence[FinalFinding], total_criteria: int) -> Coverage:
    def count(status: FindingStatus) -> int:
        return sum(1 for f in visible(finals) if f.values.status is status)

    return Coverage(
        total=total_criteria,
        found=count(FindingStatus.FOUND),
        partial=count(FindingStatus.PARTIAL),
        no_evidence=count(FindingStatus.NO_DOCUMENTARY_EVIDENCE),
        discarded=sum(1 for f in finals if f.review_status is ReviewStatus.DISCARDED),
    )


def gaps(finals: Sequence[FinalFinding]) -> list[FinalFinding]:
    pending = [f for f in visible(finals) if f.values.status is not FindingStatus.FOUND]
    return order_gaps(
        pending,
        lambda f: f.values.priority,
        lambda f: f.values.risk_level,
        lambda f: f.values.effort,
    )


def improvement_plan(finals: Sequence[FinalFinding]) -> dict[PlanPhase, list[FinalFinding]]:
    """Ordered gaps grouped by phase; empty phases are omitted."""
    plan: dict[PlanPhase, list[FinalFinding]] = {}
    for finding in gaps(finals):
        priority = finding.values.priority or Priority.MEDIUM
        plan.setdefault(_PHASE_BY_PRIORITY[priority], []).append(finding)
    return dict(sorted(plan.items()))
