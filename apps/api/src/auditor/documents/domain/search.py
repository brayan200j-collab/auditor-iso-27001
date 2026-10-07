from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ChunkHit:
    """A chunk matched by full text search, with the document's upload position in the run."""

    chunk_id: UUID
    document_id: UUID
    document_position: int
    page: int
    section: str | None
    content: str
    rank: float
