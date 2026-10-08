from __future__ import annotations

from uuid import UUID

from auditor.evaluations.application.access import EvaluationAccess
from auditor.evaluations.application.ports import AnalysisProgressReader, AnalysisRunRepository
from auditor.evaluations.application.views import EvaluationStatusView
from auditor.evaluations.domain.progress import progress
from auditor.evaluations.domain.status import EvaluationStatus
from auditor.identity.public import Permission
from auditor.shared.domain.actor import Actor


class GetEvaluationStatus:
    """Lightweight status for polling while documents are processed."""

    def __init__(
        self,
        access: EvaluationAccess,
        runs: AnalysisRunRepository,
        analysis: AnalysisProgressReader,
    ) -> None:
        self._access = access
        self._runs = runs
        self._analysis = analysis

    async def execute(self, actor: Actor, evaluation_id: UUID) -> EvaluationStatusView:
        evaluation = await self._access.require(actor, evaluation_id, Permission.VIEW_EVALUATIONS)
        counts = None
        if evaluation.status in {EvaluationStatus.ANALYZING, EvaluationStatus.FAILED}:
            counts = await self._analysis.progress(await self._runs.current(evaluation))
        return EvaluationStatusView(
            evaluation=evaluation,
            progress=progress(evaluation.status, evaluation.failed_stage),
            criteria_done=counts[0] if counts else None,
            criteria_total=counts[1] if counts else None,
        )
