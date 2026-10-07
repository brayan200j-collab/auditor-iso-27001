from __future__ import annotations

from uuid import UUID

from auditor.documents.application.ports import DocumentRepository
from auditor.documents.domain.document import Document
from auditor.evaluations.public import EvaluationAccess, EvaluationLifecycle
from auditor.identity.public import Permission
from auditor.shared.domain.actor import Actor


class ListDocuments:
    """Documents of the evaluation's current analysis run (metadata only, never storage paths)."""

    def __init__(
        self,
        access: EvaluationAccess,
        lifecycle: EvaluationLifecycle,
        documents: DocumentRepository,
    ) -> None:
        self._access = access
        self._lifecycle = lifecycle
        self._documents = documents

    async def execute(self, actor: Actor, evaluation_id: UUID) -> list[Document]:
        evaluation = await self._access.require(actor, evaluation_id, Permission.VIEW_EVALUATIONS)
        run = await self._lifecycle.current_run(evaluation)
        return await self._documents.list_for_run(run.id, evaluation.company_id)
