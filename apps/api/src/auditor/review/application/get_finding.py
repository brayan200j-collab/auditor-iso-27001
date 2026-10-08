from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from auditor.analysis.public import FindingRepository
from auditor.review.application.get_finding_history import GetFindingHistory
from auditor.review.application.get_review import GetReview, ReviewItem
from auditor.review.application.ports import HumanReviewRecord
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.errors import ResourceNotFoundError


@dataclass(frozen=True, slots=True)
class FindingDetail:
    item: ReviewItem
    evaluation_id: UUID
    evaluation_status: str
    document_names: dict[UUID, str]
    history: list[HumanReviewRecord]


class GetFinding:
    def __init__(
        self, ai_findings: FindingRepository, review: GetReview, history: GetFindingHistory
    ) -> None:
        self._ai_findings = ai_findings
        self._review = review
        self._history = history

    async def execute(self, actor: Actor, finding_id: UUID) -> FindingDetail:
        finding = await self._ai_findings.get(finding_id)
        if finding is None:
            raise ResourceNotFoundError()
        view = await self._review.execute(actor, finding.evaluation_id)
        item = next((item for item in view.items if item.ai.id == finding_id), None)
        if item is None:
            raise ResourceNotFoundError()
        return FindingDetail(
            item=item,
            evaluation_id=view.evaluation.id,
            evaluation_status=view.evaluation.status.value,
            document_names=view.document_names,
            history=await self._history.execute(actor, finding_id),
        )
