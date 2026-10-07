from __future__ import annotations

from uuid import UUID

from auditor.evaluations.application.access import EvaluationAccess
from auditor.evaluations.application.views import EvaluationStatusView
from auditor.evaluations.domain.progress import progress
from auditor.identity.public import Permission
from auditor.shared.domain.actor import Actor


class GetEvaluationStatus:
    """Lightweight status for polling while documents are processed."""

    def __init__(self, access: EvaluationAccess) -> None:
        self._access = access

    async def execute(self, actor: Actor, evaluation_id: UUID) -> EvaluationStatusView:
        evaluation = await self._access.require(actor, evaluation_id, Permission.VIEW_EVALUATIONS)
        return EvaluationStatusView(
            evaluation=evaluation, progress=progress(evaluation.status, evaluation.failed_stage)
        )
