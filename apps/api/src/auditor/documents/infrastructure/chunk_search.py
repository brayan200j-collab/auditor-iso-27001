"""Spanish full text search over the chunks of one analysis run."""

from __future__ import annotations

from functools import reduce
from uuid import UUID

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.documents.domain.search import ChunkHit
from auditor.documents.infrastructure.models import DocumentChunkModel, DocumentModel

_CONFIG = "spanish"


class FtsChunkSearch:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def search(
        self, analysis_run_id: UUID, keywords: tuple[str, ...], limit: int
    ) -> list[ChunkHit]:
        terms = [keyword.strip() for keyword in keywords if keyword.strip()]
        if not terms:
            return []
        queries: list[ColumnElement[str]] = [func.plainto_tsquery(_CONFIG, term) for term in terms]
        tsquery = reduce(lambda left, right: left.op("||")(right), queries)
        rank = func.ts_rank_cd(DocumentChunkModel.search_vector, tsquery).label("rank")
        position = (
            select(
                DocumentModel.id.label("document_id"),
                func.row_number().over(order_by=DocumentModel.created_at).label("position"),
            )
            .where(DocumentModel.analysis_run_id == analysis_run_id)
            .subquery()
        )
        rows = await self._session.execute(
            select(DocumentChunkModel, position.c.position, rank)
            .join(position, position.c.document_id == DocumentChunkModel.document_id)
            .where(
                DocumentChunkModel.analysis_run_id == analysis_run_id,
                DocumentChunkModel.search_vector.op("@@")(tsquery),
            )
            .order_by(rank.desc(), DocumentChunkModel.chunk_index)
            .limit(limit)
        )
        return [
            ChunkHit(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                document_position=int(document_position),
                page=chunk.page,
                section=chunk.section,
                content=chunk.content,
                rank=float(score),
            )
            for chunk, document_position, score in rows.all()
        ]
