from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from auditor.documents.domain.document import Document, PdfInspection


class PdfInspector(Protocol):
    async def inspect(self, data: bytes) -> PdfInspection:
        """Opens the PDF without executing anything. Raises DocumentRejectedError."""
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
