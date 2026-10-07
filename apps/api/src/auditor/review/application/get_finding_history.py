from __future__ import annotations

from uuid import UUID

from auditor.analysis.public import FindingRepository
from auditor.evaluations.public import EvaluationAccess
from auditor.identity.public import Permission
from auditor.review.application.ports import HumanReviewRecord, HumanReviewRepository
from auditor.shared.domain.actor import Actor


class GetFindingHistory:
    """Decisions taken on one finding (for the detail screen)."""

    def __init__(
        self,
        access: EvaluationAccess,
        ai_findings: FindingRepository,
        reviews: HumanReviewRepository,
    ) -> None:
        self._access = access
        self._ai_findings = ai_findings
        self._reviews = reviews

    async def execute(self, actor: Actor, finding_id: UUID) -> list[HumanReviewRecord]:
        finding = await self._ai_findings.get(finding_id)
        if finding is None:
            return []
        await self._access.require(actor, finding.evaluation_id, Permission.VIEW_AI_FINDINGS)
        return await self._reviews.history(finding_id)
