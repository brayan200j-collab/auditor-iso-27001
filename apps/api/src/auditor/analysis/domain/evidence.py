"""Evidence fragments sent to the model and verification of the citations it returns.

A citation is shown as evidence only if its text really appears in the fragment it names and that
fragment belongs to the evaluation being analysed (CLAUDE.md section 9.1).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from uuid import UUID

MIN_QUOTE_CHARS = 15
MAX_QUOTE_CHARS = 300

# Typographic quotes compare equal to plain ones (code points avoid ambiguous literals).
_QUOTES = str.maketrans(
    {
        chr(0x201C): '"',
        chr(0x201D): '"',
        chr(0x2018): "'",
        chr(0x2019): "'",
        chr(0x00AB): '"',
        chr(0x00BB): '"',
    }
)
_ANGLE = chr(0x2039)  # single left-pointing angle quotation mark


@dataclass(frozen=True, slots=True)
class EvidenceCandidate:
    """A chunk retrieved by full text search for one criterion."""

    chunk_id: UUID
    document_id: UUID
    document_alias: str
    page: int
    section: str | None
    content: str
    rank: float


@dataclass(frozen=True, slots=True)
class Citation:
    document_id: UUID
    chunk_id: UUID
    page: int
    quote: str
    citation_verified: bool


def _canonical(text: str) -> str:
    folded = unicodedata.normalize("NFKC", text).translate(_QUOTES).casefold()
    return " ".join(folded.split()).strip(" .,;:")


def quote_matches(quote: str, content: str) -> bool:
    """True if the quote is a real, reasonably sized excerpt of the content.

    Comparison ignores case, repeated whitespace (PDF line breaks) and typographic quotes.
    """
    canonical_quote = _canonical(quote)
    if not MIN_QUOTE_CHARS <= len(canonical_quote) <= MAX_QUOTE_CHARS:
        return False
    return canonical_quote in _canonical(content)


def verify_citation(
    chunk_id: UUID | None, quote: str, candidates: dict[UUID, EvidenceCandidate]
) -> Citation | None:
    """Builds the citation from the real fragment. Unknown fragments yield no citation at all,
    so the model can never invent a document or a page."""
    if chunk_id is None or chunk_id not in candidates:
        return None
    candidate = candidates[chunk_id]
    clean = " ".join(quote.split())[:MAX_QUOTE_CHARS]
    return Citation(
        document_id=candidate.document_id,
        chunk_id=candidate.chunk_id,
        page=candidate.page,
        quote=clean,
        citation_verified=quote_matches(clean, candidate.content),
    )


_TAG = re.compile(r"</?\s*(evidencia|fragmento)\b", re.IGNORECASE)


def neutralize(text: str) -> str:
    """Prevents document text from closing or opening the delimiters that mark it as data."""
    return _TAG.sub(lambda match: match.group(0).replace("<", _ANGLE), text)
