from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from auditor.retention.domain.policy import ExpiredDocument


class RetentionStore(Protocol):
    async def expired_documents(self, approved_before: datetime) -> list[ExpiredDocument]:
        """Unpurged documents of evaluations approved before the cutoff."""
        ...

    async def purge_document(self, document_id: UUID, now: datetime) -> None:
        """Deletes the text fragments and marks the document as purged (no storage path)."""
        ...
