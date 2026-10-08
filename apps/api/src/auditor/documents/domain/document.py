"""Uploaded documents and the rules they must satisfy (CLAUDE.md section 10)."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from auditor.shared.domain.errors import InvalidFileError

PDF_SIGNATURE = b"%PDF-"
PDF_MIME_TYPE = "application/pdf"
MAX_NAME_LENGTH = 150
MIN_TEXT_CHARACTERS = 40

_EXECUTABLE_EXTENSIONS = frozenset(
    {
        "exe",
        "bat",
        "cmd",
        "com",
        "js",
        "vbs",
        "ps1",
        "sh",
        "scr",
        "msi",
        "jar",
        "html",
        "htm",
        "php",
    }
)
_UNSAFE_CHARACTERS = re.compile(r'[\x00-\x1f\x7f<>:"/\\|?*]')


class DocumentStatus(StrEnum):
    STORED = "STORED"
    EXTRACTED = "EXTRACTED"
    PURGED = "PURGED"


class RejectionReason(StrEnum):
    NOT_PDF = "NOT_PDF"
    TOO_LARGE = "TOO_LARGE"
    EMPTY = "EMPTY"
    BAD_NAME = "BAD_NAME"
    CORRUPT = "CORRUPT"
    ENCRYPTED = "ENCRYPTED"
    NO_PAGES = "NO_PAGES"
    TOO_MANY_PAGES = "TOO_MANY_PAGES"
    NO_TEXT = "NO_TEXT"
    ACTIVE_CONTENT = "ACTIVE_CONTENT"
    TIMEOUT = "TIMEOUT"


REJECTION_MESSAGES: dict[RejectionReason, str] = {
    RejectionReason.NOT_PDF: "El archivo no es un PDF válido.",
    RejectionReason.TOO_LARGE: "El archivo supera el tamaño máximo de 20 MB.",
    RejectionReason.EMPTY: "El archivo está vacío.",
    RejectionReason.BAD_NAME: (
        "El nombre del archivo no es válido. Usa un nombre simple terminado en .pdf."
    ),
    RejectionReason.CORRUPT: "No pudimos abrir el PDF. Puede estar dañado.",
    RejectionReason.ENCRYPTED: (
        "El PDF está protegido con contraseña. Carga una versión sin protección."
    ),
    RejectionReason.NO_PAGES: "El PDF no tiene páginas.",
    RejectionReason.TOO_MANY_PAGES: "El PDF supera el máximo de 30 páginas.",
    RejectionReason.NO_TEXT: (
        "El PDF no tiene texto seleccionable; parece un documento escaneado. El MVP no admite OCR."
    ),
    RejectionReason.ACTIVE_CONTENT: (
        "El PDF contiene contenido activo (JavaScript o archivos adjuntos) y no se puede procesar."
    ),
    RejectionReason.TIMEOUT: (
        "El PDF tardó demasiado en procesarse. Intenta con un archivo más liviano."
    ),
}


class DocumentRejectedError(InvalidFileError):
    def __init__(self, reason: RejectionReason, detail: str | None = None) -> None:
        self.reason = reason
        super().__init__(REJECTION_MESSAGES[reason], detail=detail or reason.value)


@dataclass(frozen=True, slots=True)
class PdfInspection:
    page_count: int
    text_characters: int
    encrypted: bool
    has_javascript: bool
    has_embedded_files: bool


@dataclass(frozen=True, slots=True)
class Document:
    id: UUID
    company_id: UUID
    evaluation_id: UUID
    analysis_run_id: UUID
    original_name: str
    storage_path: str | None
    size_bytes: int
    sha256: str
    page_count: int
    has_text: bool
    status: DocumentStatus
    uploaded_by: UUID
    created_at: datetime
    extracted_at: datetime | None
    purged_at: datetime | None


def sanitize_filename(raw: str | None) -> str:
    """Display name only (never used as a path): no directories, control characters or
    double extensions; must end in .pdf."""
    if not raw:
        raise DocumentRejectedError(RejectionReason.BAD_NAME)
    name = unicodedata.normalize("NFKC", raw).replace("\\", "/").split("/")[-1].strip()
    name = _UNSAFE_CHARACTERS.sub("", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    if not name.lower().endswith(".pdf") or len(name) <= len(".pdf"):
        raise DocumentRejectedError(RejectionReason.BAD_NAME)
    stem_parts = name[: -len(".pdf")].split(".")
    if any(
        part.lower() in _EXECUTABLE_EXTENSIONS or part.lower() == "pdf" for part in stem_parts[1:]
    ):
        raise DocumentRejectedError(RejectionReason.BAD_NAME, detail="double extension")
    if len(name) > MAX_NAME_LENGTH:
        stem = name[: -len(".pdf")][: MAX_NAME_LENGTH - len(".pdf")].rstrip(" .")
        name = f"{stem}.pdf"
    return name


def check_signature(head: bytes) -> None:
    if not head.startswith(PDF_SIGNATURE):
        raise DocumentRejectedError(RejectionReason.NOT_PDF, detail="missing %PDF- signature")


def check_inspection(inspection: PdfInspection, max_pages: int) -> None:
    """Rules applied after opening the file and before any extraction."""
    if inspection.encrypted:
        raise DocumentRejectedError(RejectionReason.ENCRYPTED)
    if inspection.page_count == 0:
        raise DocumentRejectedError(RejectionReason.NO_PAGES)
    if inspection.page_count > max_pages:
        raise DocumentRejectedError(RejectionReason.TOO_MANY_PAGES)
    if inspection.has_javascript or inspection.has_embedded_files:
        raise DocumentRejectedError(RejectionReason.ACTIVE_CONTENT)
    if inspection.text_characters < MIN_TEXT_CHARACTERS:
        raise DocumentRejectedError(RejectionReason.NO_TEXT)


def storage_path(company_id: UUID, evaluation_id: UUID, document_id: UUID) -> str:
    """System-generated path; the original name is never part of it."""
    return f"companies/{company_id}/evaluations/{evaluation_id}/{document_id}.pdf"
