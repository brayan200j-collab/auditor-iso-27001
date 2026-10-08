"""The AI finding produced for one criterion. It is stored as-is and never modified afterwards;
reviewers act on it through human reviews (CLAUDE.md section 14)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from auditor.analysis.domain.evidence import Citation
from auditor.shared.domain.vocabulary import FindingStatus, Level, Priority

LOW_CONFIDENCE = Decimal("0.6")


class Outcome(StrEnum):
    OK = "OK"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class FindingDraft:
    evaluation_id: UUID
    analysis_run_id: UUID
    checklist_item_id: UUID
    criterion_code: str
    outcome: Outcome
    status: FindingStatus | None
    confidence: Decimal | None
    evidence: tuple[Citation, ...]
    gap: str
    recommendation: str
    preliminary_priority: Priority | None
    estimated_effort: Level | None
    risk_level: Level | None
    llm_called: bool
    error_summary: str | None
    provider: str
    model: str
    prompt_version: str

    @property
    def requires_human_review(self) -> bool:
        """Always true: nothing reaches the company without a person approving it."""
        return True

    @property
    def has_unverified_citations(self) -> bool:
        return any(not citation.citation_verified for citation in self.evidence)

    @property
    def needs_attention(self) -> bool:
        """Highlighted in the review queue: errors, unverified citations or low confidence."""
        return (
            self.outcome is Outcome.ERROR
            or self.has_unverified_citations
            or (self.confidence is not None and self.confidence < LOW_CONFIDENCE)
            or (
                self.status in {FindingStatus.FOUND, FindingStatus.PARTIAL}
                and not any(citation.citation_verified for citation in self.evidence)
            )
        )


@dataclass(frozen=True, slots=True)
class AIFindingRecord(FindingDraft):
    id: UUID
    created_at: datetime
