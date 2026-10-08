from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from auditor.documents.application.ports import (
    ChunkRepository,
    DocumentRepository,
    PdfTextExtractor,
)
from auditor.documents.domain.chunking import chunk_pages
from auditor.documents.domain.document import DocumentRejectedError, DocumentStatus
from auditor.shared.application.jobs import PermanentJobError
from auditor.shared.application.ports import Clock, ObjectStorage

EXTRACTION_ERROR = "EXTRACTION_ERROR"


@dataclass(frozen=True, slots=True)
class ExtractionSummary:
    documents: int
    pages: int
    chunks: int


class ExtractRunDocuments:
    """Extracts every pending document of a run into page-tagged chunks (FTS-indexed by the
    database). Idempotent: extracted documents are skipped and re-extraction replaces chunks."""

    def __init__(
        self,
        documents: DocumentRepository,
        chunks: ChunkRepository,
        storage: ObjectStorage,
        extractor: PdfTextExtractor,
        clock: Clock,
        bucket: str,
    ) -> None:
        self._documents = documents
        self._chunks = chunks
        self._storage = storage
        self._extractor = extractor
        self._clock = clock
        self._bucket = bucket

    async def execute(self, analysis_run_id: UUID, company_id: UUID) -> ExtractionSummary:
        documents = await self._documents.list_for_run(analysis_run_id, company_id)
        if not documents:
            raise PermanentJobError(EXTRACTION_ERROR, "run without documents")
        pages = 0
        for document in documents:
            pages += document.page_count
            if document.status is DocumentStatus.EXTRACTED:
                continue
            if document.storage_path is None:
                raise PermanentJobError(EXTRACTION_ERROR, "document file no longer available")
            data = await self._storage.download(self._bucket, document.storage_path)
            try:
                page_texts = await self._extractor.extract(data)
            except DocumentRejectedError as error:
                raise PermanentJobError(EXTRACTION_ERROR, error.reason.value) from error
            await self._chunks.replace_for_document(document, chunk_pages(page_texts))
            await self._documents.mark_extracted(document.id, self._clock.now())
        chunk_count = await self._chunks.count_for_run(analysis_run_id)
        if chunk_count == 0:
            raise PermanentJobError(EXTRACTION_ERROR, "no text extracted")
        return ExtractionSummary(documents=len(documents), pages=pages, chunks=chunk_count)
