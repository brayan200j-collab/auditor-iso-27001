"""Public interface of the documents module (used by the analysis pipeline and retention)."""

from auditor.documents.application.extract_documents import (
    EXTRACTION_ERROR,
    ExtractionSummary,
    ExtractRunDocuments,
)
from auditor.documents.application.ports import DocumentRepository

__all__ = [
    "EXTRACTION_ERROR",
    "DocumentRepository",
    "ExtractRunDocuments",
    "ExtractionSummary",
]
