from __future__ import annotations

from dataclasses import dataclass

from auditor.analysis.public import FindingRepository
from auditor.evaluations.public import (
    EvaluationFilters,
    EvaluationLifecycle,
    EvaluationStatus,
    EvaluationSummary,
    ListEvaluations,
)
from auditor.review.application.ports import FinalFindingRepository
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.pagination import Page, PageRequest


@dataclass(frozen=True, slots=True)
class QueueEntry:
    summary: EvaluationSummary
    findings: int
    reviewed: int


class ListReviewQueue:
    """Evaluations waiting for human review in the actor's scope, with review progress."""

    def __init__(
        self,
        evaluations: ListEvaluations,
        lifecycle: EvaluationLifecycle,
        ai_findings: FindingRepository,
        finals: FinalFindingRepository,
    ) -> None:
        self._evaluations = evaluations
        self._lifecycle = lifecycle
        self._ai_findings = ai_findings
        self._finals = finals

    async def execute(self, actor: Actor, page: PageRequest) -> Page[QueueEntry]:
        result = await self._evaluations.execute(
            actor, EvaluationFilters(status=EvaluationStatus.PENDING_REVIEW), page
        )
        entries = []
        for summary in result.items:
            run = await self._lifecycle.current_run(summary.evaluation)
            entries.append(
                QueueEntry(
                    summary=summary,
                    findings=len(await self._ai_findings.list_for_run(run.id)),
                    reviewed=len(await self._finals.list_for_run(run.id)),
                )
            )
        return Page(items=entries, total=result.total, page=result.page, page_size=result.page_size)
