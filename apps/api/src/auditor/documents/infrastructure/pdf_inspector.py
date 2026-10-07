"""PDF inspection with PyMuPDF. Nothing in the file is ever executed or rendered."""

from __future__ import annotations

import asyncio
import re

import pymupdf

from auditor.documents.domain.document import (
    MIN_TEXT_CHARACTERS,
    DocumentRejectedError,
    PdfInspection,
    RejectionReason,
)

# Whole PDF name tokens only (so a font called /JSans is not flagged).
_ACTIVE_CONTENT = re.compile(r"/(JavaScript|JS|Launch|EmbeddedFile|RichMedia)(?![A-Za-z0-9])")


def _has_active_content(document: pymupdf.Document) -> bool:
    for xref in range(1, document.xref_length()):
        try:
            source = document.xref_object(xref, compressed=True)
        except (RuntimeError, ValueError):
            continue
        if _ACTIVE_CONTENT.search(source):
            return True
    return False


def _text_characters(document: pymupdf.Document, max_pages: int) -> int:
    """Counts selectable characters, stopping as soon as there is enough evidence of text."""
    total = 0
    for index in range(min(document.page_count, max_pages)):
        total += len("".join(document.load_page(index).get_text("text").split()))
        if total >= MIN_TEXT_CHARACTERS:
            break
    return total


def inspect_pdf(data: bytes, max_pages: int) -> PdfInspection:
    try:
        document = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:  # PyMuPDF raises several exception types for broken files
        raise DocumentRejectedError(RejectionReason.CORRUPT, detail=type(exc).__name__) from exc
    try:
        if document.needs_pass or document.is_encrypted:
            return PdfInspection(
                0, 0, encrypted=True, has_javascript=False, has_embedded_files=False
            )
        page_count = document.page_count
        if page_count == 0 or page_count > max_pages:
            # Counted before extracting anything (CLAUDE.md section 10).
            return PdfInspection(
                page_count, 0, False, has_javascript=False, has_embedded_files=False
            )
        return PdfInspection(
            page_count=page_count,
            text_characters=_text_characters(document, max_pages),
            encrypted=False,
            has_javascript=_has_active_content(document),
            has_embedded_files=document.embfile_count() > 0,
        )
    except DocumentRejectedError:
        raise
    except Exception as exc:
        raise DocumentRejectedError(RejectionReason.CORRUPT, detail=type(exc).__name__) from exc
    finally:
        document.close()


class PyMuPdfInspector:
    def __init__(self, max_pages: int, timeout_seconds: float) -> None:
        self._max_pages = max_pages
        self._timeout = timeout_seconds

    async def inspect(self, data: bytes) -> PdfInspection:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(inspect_pdf, data, self._max_pages), timeout=self._timeout
            )
        except TimeoutError as exc:
            raise DocumentRejectedError(RejectionReason.TIMEOUT) from exc
