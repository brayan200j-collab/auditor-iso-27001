from __future__ import annotations

from uuid import UUID

import pytest
from hypothesis import given
from hypothesis import strategies as st

from auditor.documents.domain.document import (
    DocumentRejectedError,
    PdfInspection,
    RejectionReason,
    check_inspection,
    check_signature,
    sanitize_filename,
    storage_path,
)
from auditor.documents.infrastructure.pdf_inspector import inspect_pdf
from tests.support import pdfs


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Política de seguridad.pdf", "Política de seguridad.pdf"),
        ("informe.PDF", "informe.PDF"),
        ("../../etc/passwd.pdf", "passwd.pdf"),
        ("C:\\Users\\ana\\Documentos\\copias.pdf", "copias.pdf"),
        ("ma\x00la\x1fs.pdf", "malas.pdf"),
        ("  espacios   raros  .pdf", "espacios raros .pdf"),
        ("v1.2 política.pdf", "v1.2 política.pdf"),
    ],
)
def test_filenames_are_sanitized(raw: str, expected: str) -> None:
    assert sanitize_filename(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        None,
        "",
        ".pdf",
        "documento.docx",
        "informe.pdf.exe",
        "informe.exe.pdf",
        "a.js.pdf",
        "x.pdf.pdf",
    ],
)
def test_dangerous_or_non_pdf_names_are_rejected(raw: str | None) -> None:
    with pytest.raises(DocumentRejectedError) as error:
        sanitize_filename(raw)
    assert error.value.reason is RejectionReason.BAD_NAME


def test_long_names_are_truncated_keeping_the_extension() -> None:
    name = sanitize_filename("a" * 400 + ".pdf")
    assert len(name) == 150
    assert name.endswith(".pdf")


@given(st.text(max_size=300))
def test_sanitized_names_never_contain_paths_or_control_characters(raw: str) -> None:
    try:
        name = sanitize_filename(raw + ".pdf")
    except DocumentRejectedError:
        return
    assert "/" not in name
    assert "\\" not in name
    assert all(ord(character) >= 32 for character in name)
    assert name.lower().endswith(".pdf")


def test_signature_check() -> None:
    check_signature(b"%PDF-1.7")
    with pytest.raises(DocumentRejectedError):
        check_signature(b"MZ\x90\x00")


@pytest.mark.parametrize(
    ("inspection", "reason"),
    [
        (PdfInspection(3, 500, True, False, False), RejectionReason.ENCRYPTED),
        (PdfInspection(0, 0, False, False, False), RejectionReason.NO_PAGES),
        (PdfInspection(31, 900, False, False, False), RejectionReason.TOO_MANY_PAGES),
        (PdfInspection(3, 900, False, True, False), RejectionReason.ACTIVE_CONTENT),
        (PdfInspection(3, 900, False, False, True), RejectionReason.ACTIVE_CONTENT),
        (PdfInspection(3, 10, False, False, False), RejectionReason.NO_TEXT),
    ],
)
def test_inspection_rules(inspection: PdfInspection, reason: RejectionReason) -> None:
    with pytest.raises(DocumentRejectedError) as error:
        check_inspection(inspection, max_pages=30)
    assert error.value.reason is reason


def test_storage_path_never_contains_the_original_name() -> None:
    company, evaluation, document = (UUID(int=1), UUID(int=2), UUID(int=3))
    assert storage_path(company, evaluation, document) == (
        f"companies/{company}/evaluations/{evaluation}/{document}.pdf"
    )


# ------------------------------------------------------------------ real PyMuPDF inspection


def test_synthetic_policy_passes_inspection() -> None:
    inspection = inspect_pdf(pdfs.policy_pdf(), max_pages=30)
    assert inspection.page_count == len(pdfs.POLICY_PAGES)
    check_inspection(inspection, max_pages=30)


def test_thirty_pages_are_accepted() -> None:
    check_inspection(inspect_pdf(pdfs.many_pages_pdf(30), max_pages=30), max_pages=30)


@pytest.mark.parametrize(
    ("build", "reason"),
    [
        (pdfs.scanned_pdf, RejectionReason.NO_TEXT),
        (pdfs.encrypted_pdf, RejectionReason.ENCRYPTED),
        (pdfs.javascript_pdf, RejectionReason.ACTIVE_CONTENT),
        (pdfs.attachment_pdf, RejectionReason.ACTIVE_CONTENT),
        (lambda: pdfs.many_pages_pdf(31), RejectionReason.TOO_MANY_PAGES),
    ],
)
def test_hostile_pdfs_are_rejected(build: object, reason: RejectionReason) -> None:
    assert callable(build)
    with pytest.raises(DocumentRejectedError) as error:
        check_inspection(inspect_pdf(build(), max_pages=30), max_pages=30)
    assert error.value.reason is reason


def test_corrupt_pdf_is_rejected() -> None:
    with pytest.raises(DocumentRejectedError) as error:
        check_inspection(inspect_pdf(pdfs.corrupt_pdf(), max_pages=30), max_pages=30)
    assert error.value.reason in {RejectionReason.CORRUPT, RejectionReason.NO_PAGES}
