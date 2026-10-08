"""Splits extracted page text into bounded, overlapping chunks that keep page and section.

Rules (CLAUDE.md section 10): chunks never cross pages (traceability), stay below a maximum size,
try not to cut sentences, carry a small overlap, and remember the last detected section heading.
Numbered headings ("5. Gestión de activos") are recognized per line, before sentence splitting,
and always start a new chunk.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

TARGET_CHARS = 900
MAX_CHARS = 1200
OVERLAP_CHARS = 150
MAX_SECTION_CHARS = 200

_SENTENCE_END = re.compile(r"(?<=[.!?;])\s+")
_HEADING = re.compile(r"^\s*(\d+(?:\.\d+)*)\.?\s+([A-ZÁÉÍÓÚÑ][^\n]{2,120})$")


@dataclass(frozen=True, slots=True)
class PageText:
    number: int
    text: str


@dataclass(frozen=True, slots=True)
class Chunk:
    page: int
    index: int
    section: str | None
    content: str


@dataclass(frozen=True, slots=True)
class _Unit:
    text: str
    heading: str | None = None


def normalize(text: str) -> str:
    """Collapses spaces inside lines and keeps paragraph breaks."""
    lines = [" ".join(line.split()) for line in text.replace("\r", "\n").split("\n")]
    joined = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", joined).strip()


def _split_long(sentence: str) -> list[str]:
    parts: list[str] = []
    rest = sentence
    while len(rest) > MAX_CHARS:  # an endless "sentence": cut on a space if possible
        cut = rest.rfind(" ", 0, MAX_CHARS)
        cut = cut if cut > MAX_CHARS // 2 else MAX_CHARS
        parts.append(rest[:cut].strip())
        rest = rest[cut:].strip()
    if rest:
        parts.append(rest)
    return parts


def _paragraph_units(lines: list[str]) -> list[_Unit]:
    paragraph = " ".join(line for line in lines if line).strip()
    if not paragraph:
        return []
    return [
        _Unit(part)
        for sentence in _SENTENCE_END.split(paragraph)
        if sentence.strip()
        for part in _split_long(sentence.strip())
    ]


def _units(text: str) -> list[_Unit]:
    units: list[_Unit] = []
    buffer: list[str] = []
    for line in normalize(text).split("\n"):
        match = _HEADING.match(line)
        if match:
            units.extend(_paragraph_units(buffer))
            buffer = []
            label = f"{match.group(1)}. {match.group(2).strip()}"[:MAX_SECTION_CHARS]
            units.extend(_Unit(part, heading=label) for part in _split_long(line.strip())[:1])
        elif not line:
            units.extend(_paragraph_units(buffer))
            buffer = []
        else:
            buffer.append(line)
    units.extend(_paragraph_units(buffer))
    return units


def _overlap(sentences: list[str]) -> list[str]:
    carried: list[str] = []
    size = 0
    for sentence in reversed(sentences):
        if size + len(sentence) > OVERLAP_CHARS:
            break
        carried.insert(0, sentence)
        size += len(sentence) + 1
    return carried


def _emit(chunks: list[Chunk], page: int, section: str | None, parts: list[str]) -> None:
    content = " ".join(parts).strip()
    if content:
        chunks.append(Chunk(page, len(chunks), section, content))


def chunk_pages(pages: list[PageText]) -> list[Chunk]:
    chunks: list[Chunk] = []
    section: str | None = None
    for page in pages:
        current: list[str] = []
        chunk_section = section
        for unit in _units(page.text):
            if unit.heading:
                _emit(chunks, page.number, chunk_section, current)
                current = []
                section = unit.heading
                chunk_section = section
            elif current and sum(len(item) + 1 for item in current) + len(unit.text) > TARGET_CHARS:
                _emit(chunks, page.number, chunk_section, current)
                current = _overlap(current)
            current.append(unit.text)
        _emit(chunks, page.number, chunk_section, current)
    return chunks
