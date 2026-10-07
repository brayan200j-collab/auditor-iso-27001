from __future__ import annotations

import hashlib
from dataclasses import dataclass
from uuid import UUID, uuid4

from auditor.documents.application.ports import (
    DocumentRepository,
    FileScanner,
    NewDocument,
    PdfInspector,
)
from auditor.documents.domain.document import (
    PDF_MIME_TYPE,
    Document,
    DocumentRejectedError,
    RejectionReason,
    check_inspection,
    check_signature,
    sanitize_filename,
    storage_path,
)
from auditor.evaluations.public import (
    CURRENT_CONSENT,
    ConsentRepository,
    Evaluation,
    EvaluationAccess,
    EvaluationLifecycle,
    EvaluationStatus,
    Party,
    Trigger,
)
from auditor.identity.public import Permission
from auditor.shared.application.ports import AuditLogger, ObjectStorage, UnitOfWork
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.audit import AuditAction, AuditEntry, AuditOutcome
from auditor.shared.domain.errors import (
    ConflictError,
    InvalidStateTransitionError,
    QuotaExceededError,
)

_TRIGGER_BY_STATUS = {
    EvaluationStatus.DRAFT: Trigger.DOCUMENT_UPLOADED,
    EvaluationStatus.RECEIVED: Trigger.DOCUMENT_UPLOADED,
    EvaluationStatus.REJECTED: Trigger.NEW_DOCUMENT_AFTER_REJECTION,
}


@dataclass(frozen=True, slots=True)
class UploadLimits:
    max_bytes: int
    max_pages: int
    max_documents: int
    bucket: str


@dataclass(frozen=True, slots=True)
class IncomingFile:
    filename: str | None
    content_type: str | None
    data: bytes


class UploadDocument:
    """Validates a PDF end to end, stores it privately and moves the evaluation forward."""

    def __init__(
        self,
        access: EvaluationAccess,
        lifecycle: EvaluationLifecycle,
        consents: ConsentRepository,
        documents: DocumentRepository,
        storage: ObjectStorage,
        inspector: PdfInspector,
        scanner: FileScanner,
        audit: AuditLogger,
        uow: UnitOfWork,
        limits: UploadLimits,
    ) -> None:
        self._access = access
        self._lifecycle = lifecycle
        self._consents = consents
        self._documents = documents
        self._storage = storage
        self._inspector = inspector
        self._scanner = scanner
        self._audit = audit
        self._uow = uow
        self._limits = limits

    async def execute(self, actor: Actor, evaluation_id: UUID, file: IncomingFile) -> Document:
        evaluation = await self._access.require(actor, evaluation_id, Permission.UPLOAD_DOCUMENTS)
        trigger = _TRIGGER_BY_STATUS.get(evaluation.status)
        if trigger is None:
            raise InvalidStateTransitionError(
                "No es posible cargar documentos en el estado actual de la evaluación."
            )
        if not await self._consents.has_consent(
            evaluation.id, actor.user_id, CURRENT_CONSENT.version
        ):
            raise ConflictError("Debes aceptar el consentimiento antes de cargar documentos.")
        try:
            name, inspection_pages = await self._validate(file)
        except DocumentRejectedError as rejection:
            await self._record_rejection(actor, evaluation, rejection.reason)
            raise
        return await self._store(actor, evaluation, trigger, file, name, inspection_pages)

    async def _validate(self, file: IncomingFile) -> tuple[str, int]:
        name = sanitize_filename(file.filename)
        if (file.content_type or "").split(";")[0].strip().lower() != PDF_MIME_TYPE:
            raise DocumentRejectedError(RejectionReason.NOT_PDF, detail="declared MIME type")
        if not file.data:
            raise DocumentRejectedError(RejectionReason.EMPTY)
        if len(file.data) > self._limits.max_bytes:
            raise DocumentRejectedError(RejectionReason.TOO_LARGE)
        check_signature(file.data[:8])
        inspection = await self._inspector.inspect(file.data)
        check_inspection(inspection, self._limits.max_pages)
        await self._scanner.scan(file.data)
        return name, inspection.page_count

    async def _store(
        self,
        actor: Actor,
        evaluation: Evaluation,
        trigger: Trigger,
        file: IncomingFile,
        name: str,
        page_count: int,
    ) -> Document:
        updated = await self._lifecycle.transition(
            evaluation, trigger, Party.SME, actor_id=actor.user_id, actor_role=actor.role
        )
        run = await self._lifecycle.current_run(updated)
        if await self._documents.count_for_run(run.id) >= self._limits.max_documents:
            raise QuotaExceededError(
                "Alcanzaste el máximo de documentos permitidos para esta evaluación."
            )
        document_id = uuid4()
        path = storage_path(evaluation.company_id, evaluation.id, document_id)
        await self._storage.upload(self._limits.bucket, path, file.data, PDF_MIME_TYPE)
        try:
            document = await self._documents.add(
                NewDocument(
                    id=document_id,
                    company_id=evaluation.company_id,
                    evaluation_id=evaluation.id,
                    analysis_run_id=run.id,
                    original_name=name,
                    storage_path=path,
                    size_bytes=len(file.data),
                    sha256=hashlib.sha256(file.data).hexdigest(),
                    page_count=page_count,
                    has_text=True,
                    uploaded_by=actor.user_id,
                )
            )
            await self._audit.record(
                AuditEntry(
                    action=AuditAction.DOCUMENT_UPLOADED,
                    actor_id=actor.user_id,
                    actor_role=actor.role,
                    company_id=evaluation.company_id,
                    resource_type="document",
                    resource_id=document_id,
                    details={
                        "evaluation_id": str(evaluation.id),
                        "pages": page_count,
                        "size_bytes": len(file.data),
                    },
                )
            )
            await self._uow.commit()
        except Exception:
            await self._uow.rollback()
            await self._storage.delete(self._limits.bucket, path)
            raise
        return document

    async def _record_rejection(
        self, actor: Actor, evaluation: Evaluation, reason: RejectionReason
    ) -> None:
        await self._audit.record_immediately(
            AuditEntry(
                action=AuditAction.DOCUMENT_REJECTED,
                outcome=AuditOutcome.FAILURE,
                actor_id=actor.user_id,
                actor_role=actor.role,
                company_id=evaluation.company_id,
                resource_type="evaluation",
                resource_id=evaluation.id,
                details={"reason": reason.value},
            )
        )
