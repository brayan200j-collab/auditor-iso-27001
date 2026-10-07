from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from auditor.analysis.public import AIFindingRecord, FindingRepository
from auditor.checklist.public import ChecklistItem, ChecklistRepository
from auditor.documents.public import DocumentRepository
from auditor.evaluations.public import Evaluation, EvaluationAccess, EvaluationLifecycle
from auditor.identity.public import Permission
from auditor.review.application.ports import (
    FinalFindingRepository,
)
from auditor.review.domain.review import FinalFinding
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.vocabulary import ReviewStatus


@dataclass(frozen=True, slots=True)
class ReviewItem:
    ai: AIFindingRecord
    criterion: ChecklistItem
    final: FinalFinding | None

    @property
    def review_status(self) -> ReviewStatus:
        return self.final.review_status if self.final else ReviewStatus.PENDING_REVIEW


@dataclass(frozen=True, slots=True)
class ReviewSummary:
    total: int
    found: int
    partial: int
    no_evidence: int
    errors: int
    reviewed: int
    needs_attention: int

    @property
    def pending(self) -> int:
        return self.total - self.reviewed


@dataclass(frozen=True, slots=True)
class ReviewView:
    evaluation: Evaluation
    items: list[ReviewItem]
    summary: ReviewSummary
    document_names: dict[UUID, str]


def queue_key(item: ReviewItem) -> tuple[int, int, Decimal, str]:
    """Pending first; within them, findings needing attention and low confidence first."""
    confidence = item.ai.confidence if item.ai.confidence is not None else Decimal(2)
    return (
        0 if item.final is None else 1,
        0 if item.ai.needs_attention else 1,
        confidence,
        item.ai.criterion_code,
    )


def summarize(items: list[ReviewItem]) -> ReviewSummary:
    statuses = Counter(item.ai.status.value if item.ai.status else "ERROR" for item in items)
    return ReviewSummary(
        total=len(items),
        found=statuses["FOUND"],
        partial=statuses["PARTIAL"],
        no_evidence=statuses["NO_DOCUMENTARY_EVIDENCE"],
        errors=statuses["ERROR"],
        reviewed=sum(1 for item in items if item.final is not None),
        needs_attention=sum(1 for item in items if item.ai.needs_attention),
    )


class GetReview:
    def __init__(
        self,
        access: EvaluationAccess,
        lifecycle: EvaluationLifecycle,
        ai_findings: FindingRepository,
        finals: FinalFindingRepository,
        checklists: ChecklistRepository,
        documents: DocumentRepository,
    ) -> None:
        self._access = access
        self._lifecycle = lifecycle
        self._ai_findings = ai_findings
        self._finals = finals
        self._checklists = checklists
        self._documents = documents

    async def execute(self, actor: Actor, evaluation_id: UUID) -> ReviewView:
        evaluation = await self._access.require(actor, evaluation_id, Permission.VIEW_AI_FINDINGS)
        run = await self._lifecycle.current_run(evaluation)
        findings = await self._ai_findings.list_for_run(run.id)
        finals = {final.ai_finding_id: final for final in await self._finals.list_for_run(run.id)}
        version = (
            await self._checklists.get(run.checklist_version_id)
            if run.checklist_version_id
            else None
        )
        criteria = {item.id: item for item in version.items} if version else {}
        items = sorted(
            (
                ReviewItem(
                    ai=finding,
                    criterion=criteria[finding.checklist_item_id],
                    final=finals.get(finding.id),
                )
                for finding in findings
                if finding.checklist_item_id in criteria
            ),
            key=queue_key,
        )
        documents = await self._documents.list_for_run(run.id, evaluation.company_id)
        return ReviewView(
            evaluation=evaluation,
            items=items,
            summary=summarize(items),
            document_names={document.id: document.original_name for document in documents},
        )
