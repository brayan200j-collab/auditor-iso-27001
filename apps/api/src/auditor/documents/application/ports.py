from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from auditor.documents.domain.chunking import Chunk, PageText
from auditor.documents.domain.document import Document, PdfInspection


class PdfInspector(Protocol):
    async def inspect(self, data: bytes) -> PdfInspection:
        """Opens the PDF without executing anything. Raises DocumentRejectedError."""
        ...


class PdfTextExtractor(Protocol):
    async def extract(self, data: bytes) -> list[PageText]:
        """Text per page (1-based numbers). Raises DocumentRejectedError for unreadable files."""
        ...


class FileScanner(Protocol):
    """Extension point for antivirus scanning (not implemented in the MVP)."""

    async def scan(self, data: bytes) -> None: ...


class NoopFileScanner:
    async def scan(self, data: bytes) -> None:
        return None


@dataclass(frozen=True, slots=True)
class NewDocument:
    id: UUID
    company_id: UUID
    evaluation_id: UUID
    analysis_run_id: UUID
    original_name: str
    storage_path: str
    size_bytes: int
    sha256: str
    page_count: int
    has_text: bool
    uploaded_by: UUID


class DocumentRepository(Protocol):
    async def add(self, document: NewDocument) -> Document: ...

    async def get(
        self, document_id: UUID, evaluation_id: UUID, company_id: UUID
    ) -> Document | None:
        """Always scoped by evaluation and company."""
        ...

    async def list_for_run(self, analysis_run_id: UUID, company_id: UUID) -> list[Document]: ...

    async def count_for_run(self, analysis_run_id: UUID) -> int: ...

    async def delete(self, document_id: UUID) -> None: ...

    async def mark_extracted(self, document_id: UUID, now: datetime) -> None: ...

    async def all_extracted(self, analysis_run_id: UUID) -> bool: ...


class ChunkRepository(Protocol):
    async def replace_for_document(self, document: Document, chunks: list[Chunk]) -> None:
        """Deletes previous chunks of the document and stores the new ones (idempotent)."""
        ...

    async def count_for_run(self, analysis_run_id: UUID) -> int: ...
