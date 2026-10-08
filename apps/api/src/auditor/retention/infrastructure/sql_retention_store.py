"""Data-lifecycle adapter: works directly on the documents tables with plain SQL so the
retention module does not depend on another module's internals."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.retention.domain.policy import ExpiredDocument

_EXPIRED = text(
    """
    SELECT d.id, d.evaluation_id, d.company_id, d.storage_path
    FROM documents d
    JOIN evaluations e ON e.id = d.evaluation_id
    WHERE e.status = 'APPROVED'
      AND e.approved_at < :cutoff
      AND d.purged_at IS NULL
    ORDER BY d.evaluation_id, d.created_at
    """
)
_DELETE_CHUNKS = text("DELETE FROM document_chunks WHERE document_id = :document_id")
_MARK_PURGED = text(
    """
    UPDATE documents
    SET status = 'PURGED', storage_path = NULL, purged_at = :now
    WHERE id = :document_id
    """
)


class SqlRetentionStore:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def expired_documents(self, approved_before: datetime) -> list[ExpiredDocument]:
        rows = await self._session.execute(_EXPIRED, {"cutoff": approved_before})
        return [
            ExpiredDocument(
                id=row.id,
                evaluation_id=row.evaluation_id,
                company_id=row.company_id,
                storage_path=row.storage_path,
            )
            for row in rows
        ]

    async def purge_document(self, document_id: UUID, now: datetime) -> None:
        await self._session.execute(_DELETE_CHUNKS, {"document_id": document_id})
        await self._session.execute(_MARK_PURGED, {"document_id": document_id, "now": now})
