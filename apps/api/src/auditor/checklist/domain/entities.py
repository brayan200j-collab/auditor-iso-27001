"""Versioned checklist.

Published versions are immutable; an evaluation stays bound to the version it ran with.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from auditor.shared.domain.vocabulary import Level, Priority

CODE_PATTERN = re.compile(r"^ISO-\d{2}$")


class VersionStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"


class ReferenceStatus(StrEnum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"


@dataclass(frozen=True, slots=True)
class ChecklistItem:
    id: UUID
    code: str
    position: int
    name: str
    description: str
    evaluation_question: str
    expected_evidence: str
    iso_reference: str | None
    cis_reference: str | None
    nist_reference: str | None
    reference_status: ReferenceStatus
    keywords: tuple[str, ...]
    priority: Priority
    risk_level: Level
    effort: Level
    active: bool = True

    @property
    def label(self) -> str:
        return f"{self.code} · {self.name}"


@dataclass(frozen=True, slots=True)
class ChecklistVersion:
    id: UUID
    version: int
    label: str
    status: VersionStatus
    published_at: datetime | None
    items: tuple[ChecklistItem, ...] = field(default_factory=tuple)

    @property
    def is_published(self) -> bool:
        return self.status is VersionStatus.PUBLISHED

    @property
    def active_items(self) -> tuple[ChecklistItem, ...]:
        return tuple(item for item in self.items if item.active)


def is_valid_code(code: str) -> bool:
    return bool(CODE_PATTERN.match(code))
