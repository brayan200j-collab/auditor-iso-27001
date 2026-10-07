from __future__ import annotations

from typing import Protocol
from uuid import UUID

from auditor.analysis.domain.evidence import EvidenceCandidate
from auditor.documents.public import ChunkHit


class ChunkSearch(Protocol):
    async def search(
        self, analysis_run_id: UUID, keywords: tuple[str, ...], limit: int
    ) -> list[ChunkHit]: ...


class DocumentEvidenceSearch:
    """Adapts the documents module's full text search to evidence candidates. Original file
    names never reach the model: documents are referred to as "Documento N"."""

    def __init__(self, chunks: ChunkSearch) -> None:
        self._chunks = chunks

    async def search(
        self, analysis_run_id: UUID, keywords: tuple[str, ...], limit: int
    ) -> list[EvidenceCandidate]:
        hits = await self._chunks.search(analysis_run_id, keywords, limit)
        return [
            EvidenceCandidate(
                chunk_id=hit.chunk_id,
                document_id=hit.document_id,
                document_alias=f"Documento {hit.document_position}",
                page=hit.page,
                section=hit.section,
                content=hit.content,
                rank=hit.rank,
            )
            for hit in hits
        ]
