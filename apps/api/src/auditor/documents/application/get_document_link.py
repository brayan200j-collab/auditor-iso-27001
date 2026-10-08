from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from auditor.documents.application.ports import DocumentRepository
from auditor.evaluations.public import EvaluationAccess
from auditor.identity.public import Permission
from auditor.shared.application.ports import AuditLogger, ObjectStorage, UnitOfWork
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.audit import AuditAction, AuditEntry
from auditor.shared.domain.errors import ConflictError, ResourceNotFoundError


class DocumentPurgedError(ConflictError):
    default_message = (
        "El PDF original ya no está disponible: se eliminó según la política de retención. "
        "Los hallazgos y el informe se conservan."
    )


@dataclass(frozen=True, slots=True)
class DocumentLink:
    url: str
    expires_in: int


class GetDocumentLink:
    """Short-lived link to view an evaluation's original PDF (assigned reviewer, admin or the
    owning company), so the reviewer can check where each AI conclusion came from. Audited."""

    def __init__(
        self,
        access: EvaluationAccess,
        documents: DocumentRepository,
        storage: ObjectStorage,
        audit: AuditLogger,
        uow: UnitOfWork,
        bucket: str,
        ttl_seconds: int,
    ) -> None:
        self._access = access
        self._documents = documents
        self._storage = storage
        self._audit = audit
        self._uow = uow
        self._bucket = bucket
        self._ttl = ttl_seconds

    async def execute(self, actor: Actor, evaluation_id: UUID, document_id: UUID) -> DocumentLink:
        evaluation = await self._access.require(actor, evaluation_id, Permission.VIEW_EVALUATIONS)
        document = await self._documents.get(document_id, evaluation.id, evaluation.company_id)
        if document is None:
            raise ResourceNotFoundError()
        if not document.storage_path or document.purged_at is not None:
            raise DocumentPurgedError()
        url = await self._storage.create_signed_url(
            self._bucket, document.storage_path, self._ttl, None
        )
        await self._audit.record(
            AuditEntry(
                action=AuditAction.DOCUMENT_VIEWED,
                actor_id=actor.user_id,
                actor_role=actor.role.value,
                company_id=evaluation.company_id,
                resource_type="document",
                resource_id=document.id,
                details={"evaluation_id": str(evaluation.id)},
            )
        )
        await self._uow.commit()
        return DocumentLink(url=url, expires_in=self._ttl)
