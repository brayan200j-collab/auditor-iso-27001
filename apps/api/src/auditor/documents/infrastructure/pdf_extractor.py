"""Per-page text extraction with PyMuPDF (no rendering, no OCR, nothing executed)."""

from __future__ import annotations

import asyncio

import pymupdf

from auditor.documents.domain.chunking import PageText
from auditor.documents.domain.document import DocumentRejectedError, RejectionReason


def extract_pages(data: bytes, max_pages: int) -> list[PageText]:
    try:
        document = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise DocumentRejectedError(RejectionReason.CORRUPT, detail=type(exc).__name__) from exc
    try:
        if document.needs_pass or document.is_encrypted:
            raise DocumentRejectedError(RejectionReason.ENCRYPTED)
        if document.page_count > max_pages:
            raise DocumentRejectedError(RejectionReason.TOO_MANY_PAGES)
        return [
            PageText(number=index + 1, text=document.load_page(index).get_text("text", sort=True))
            for index in range(document.page_count)
        ]
    finally:
        document.close()


class PyMuPdfExtractor:
    def __init__(self, max_pages: int, timeout_seconds: float) -> None:
        self._max_pages = max_pages
        self._timeout = timeout_seconds

    async def extract(self, data: bytes) -> list[PageText]:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(extract_pages, data, self._max_pages), timeout=self._timeout
            )
        except TimeoutError as exc:
            raise DocumentRejectedError(RejectionReason.TIMEOUT) from exc
