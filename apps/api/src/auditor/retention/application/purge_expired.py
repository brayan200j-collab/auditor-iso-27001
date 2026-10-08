from __future__ import annotations

import contextlib
from collections import defaultdict
from uuid import UUID

from auditor.identity.public import Permission, authorize
from auditor.retention.application.ports import RetentionStore
from auditor.retention.domain.policy import ExpiredDocument, PurgeSummary, purge_cutoff
from auditor.shared.application.ports import AuditLogger, Clock, ObjectStorage, UnitOfWork
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.audit import AuditAction, AuditEntry
from auditor.shared.domain.errors import ResourceNotFoundError


class PurgeExpiredDocuments:
    """Deletes original PDFs and fragments past the retention period, one evaluation at a time.

    Runs periodically in the background and on demand by an administrator. Each evaluation is
    committed separately, so an interruption never leaves half-purged evaluations unaudited.
    """

    def __init__(
        self,
        store: RetentionStore,
        storage: ObjectStorage,
        audit: AuditLogger,
        uow: UnitOfWork,
        clock: Clock,
        bucket: str,
        retention_days: int,
    ) -> None:
        self._store = store
        self._storage = storage
        self._audit = audit
        self._uow = uow
        self._clock = clock
        self._bucket = bucket
        self._retention_days = retention_days

    async def execute(self, actor: Actor | None = None) -> PurgeSummary:
        if actor is not None:
            authorize(actor, Permission.MANAGE_RETENTION)
        now = self._clock.now()
        expired = await self._store.expired_documents(purge_cutoff(now, self._retention_days))
        by_evaluation: dict[UUID, list[ExpiredDocument]] = defaultdict(list)
        for document in expired:
            by_evaluation[document.evaluation_id].append(document)

        for evaluation_id, documents in by_evaluation.items():
            for document in documents:
                if document.storage_path:
                    # An object that is already gone still gets its row marked as purged.
                    with contextlib.suppress(ResourceNotFoundError):
                        await self._storage.delete(self._bucket, document.storage_path)
                await self._store.purge_document(document.id, now)
            await self._audit.record(
                AuditEntry(
                    action=AuditAction.RETENTION_PURGED,
                    actor_id=actor.user_id if actor else None,
                    actor_role=actor.role.value if actor else None,
                    company_id=documents[0].company_id,
                    resource_type="evaluation",
                    resource_id=evaluation_id,
                    details={
                        "documents": len(documents),
                        "retention_days": self._retention_days,
                    },
                )
            )
            await self._uow.commit()
        return PurgeSummary(evaluations=len(by_evaluation), documents=len(expired))
