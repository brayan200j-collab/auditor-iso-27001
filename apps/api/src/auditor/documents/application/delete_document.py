from __future__ import annotations

from uuid import UUID

from auditor.documents.application.ports import DocumentRepository
from auditor.evaluations.public import (
    EvaluationAccess,
    EvaluationLifecycle,
    EvaluationStatus,
    Party,
    Trigger,
)
from auditor.identity.public import Permission
from auditor.shared.application.ports import AuditLogger, ObjectStorage, UnitOfWork
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.audit import AuditAction, AuditEntry
from auditor.shared.domain.errors import InvalidStateTransitionError, ResourceNotFoundError

_DELETABLE = {EvaluationStatus.DRAFT, EvaluationStatus.RECEIVED}


class DeleteDocument:
    """Removes a document (file and record) before the analysis starts. Audited."""

    def __init__(
        self,
        access: EvaluationAccess,
        lifecycle: EvaluationLifecycle,
        documents: DocumentRepository,
        storage: ObjectStorage,
        audit: AuditLogger,
        uow: UnitOfWork,
        bucket: str,
    ) -> None:
        self._access = access
        self._lifecycle = lifecycle
        self._documents = documents
        self._storage = storage
        self._audit = audit
        self._uow = uow
        self._bucket = bucket

    async def execute(self, actor: Actor, evaluation_id: UUID, document_id: UUID) -> None:
        evaluation = await self._access.require(actor, evaluation_id, Permission.UPLOAD_DOCUMENTS)
        document = await self._documents.get(document_id, evaluation.id, evaluation.company_id)
        if document is None:
            raise ResourceNotFoundError()
        if evaluation.status not in _DELETABLE:
            raise InvalidStateTransitionError(
                "Los documentos ya no se pueden eliminar en el estado actual de la evaluación."
            )
        run = await self._lifecycle.current_run(evaluation)
        if document.analysis_run_id != run.id:
            raise InvalidStateTransitionError()

        await self._documents.delete(document.id)
        remaining = await self._documents.count_for_run(run.id)
        if remaining == 0 and evaluation.status is EvaluationStatus.RECEIVED:
            await self._lifecycle.transition(
                evaluation,
                Trigger.LAST_DOCUMENT_DELETED,
                Party.SME,
                actor_id=actor.user_id,
                actor_role=actor.role,
            )
        await self._audit.record(
            AuditEntry(
                action=AuditAction.DOCUMENT_DELETED,
                actor_id=actor.user_id,
                actor_role=actor.role,
                company_id=evaluation.company_id,
                resource_type="document",
                resource_id=document.id,
                details={"evaluation_id": str(evaluation.id)},
            )
        )
        await self._uow.commit()
        if document.storage_path:
            await self._storage.delete(self._bucket, document.storage_path)
