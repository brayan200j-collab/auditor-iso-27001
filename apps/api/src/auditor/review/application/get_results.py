from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from auditor.checklist.public import ChecklistItem, ChecklistRepository
from auditor.documents.public import DocumentRepository
from auditor.evaluations.public import (
    Evaluation,
    EvaluationAccess,
    EvaluationLifecycle,
    EvaluationStatus,
)
from auditor.identity.public import Permission
from auditor.review.application.ports import FinalFindingRepository
from auditor.review.domain.results import (
    Coverage,
    PlanPhase,
    coverage,
    gaps,
    improvement_plan,
    visible,
)
from auditor.review.domain.review import FinalFinding
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.errors import ConflictError


class ResultsNotAvailableError(ConflictError):
    default_message = "Los resultados estarán disponibles cuando termine la revisión humana."


@dataclass(frozen=True, slots=True)
class ResultItem:
    final: FinalFinding
    criterion: ChecklistItem


@dataclass(frozen=True, slots=True)
class ResultsView:
    evaluation: Evaluation
    items: list[ResultItem]
    coverage: Coverage
    gaps: list[ResultItem]
    plan: dict[PlanPhase, list[ResultItem]]
    document_names: dict[UUID, str]
    documents_retained_until: datetime | None


class GetApprovedResults:
    """Reviewed results of an approved evaluation; nothing is shown before approval."""

    def __init__(
        self,
        access: EvaluationAccess,
        lifecycle: EvaluationLifecycle,
        finals: FinalFindingRepository,
        checklists: ChecklistRepository,
        documents: DocumentRepository,
        retention_days: int,
    ) -> None:
        self._retention = timedelta(days=retention_days)
        self._access = access
        self._lifecycle = lifecycle
        self._finals = finals
        self._checklists = checklists
        self._documents = documents

    async def execute(self, actor: Actor, evaluation_id: UUID) -> ResultsView:
        evaluation = await self._access.require(
            actor, evaluation_id, Permission.VIEW_APPROVED_RESULTS
        )
        return await self.for_evaluation(evaluation)

    async def for_evaluation(self, evaluation: Evaluation) -> ResultsView:
        """Also used by the report step, which runs without a request."""
        if evaluation.status is not EvaluationStatus.APPROVED:
            raise ResultsNotAvailableError()
        run = await self._lifecycle.current_run(evaluation)
        version = (
            await self._checklists.get(run.checklist_version_id)
            if run.checklist_version_id
            else None
        )
        criteria = {item.id: item for item in version.items} if version else {}
        finals = [
            f for f in await self._finals.list_for_run(run.id) if f.checklist_item_id in criteria
        ]

        def item(final: FinalFinding) -> ResultItem:
            return ResultItem(final=final, criterion=criteria[final.checklist_item_id])

        documents = await self._documents.list_for_run(run.id, evaluation.company_id)
        return ResultsView(
            evaluation=evaluation,
            items=[item(f) for f in sorted(visible(finals), key=lambda f: f.criterion_code)],
            coverage=coverage(finals, len(criteria)),
            gaps=[item(f) for f in gaps(finals)],
            plan={
                phase: [item(f) for f in group] for phase, group in improvement_plan(finals).items()
            },
            document_names={d.id: d.original_name for d in documents},
            documents_retained_until=(
                evaluation.approved_at + self._retention if evaluation.approved_at else None
            ),
        )
