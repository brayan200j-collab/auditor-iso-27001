from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from auditor.review.domain.review import FinalFinding, ReviewDecision


@dataclass(frozen=True, slots=True)
class FindingKey:
    ai_finding_id: UUID
    evaluation_id: UUID
    analysis_run_id: UUID
    checklist_item_id: UUID
    criterion_code: str


class FinalFindingRepository(Protocol):
    async def get_for_ai_finding(self, ai_finding_id: UUID) -> FinalFinding | None: ...

    async def save(
        self, key: FindingKey, decision: ReviewDecision, reviewer_id: UUID, now: datetime
    ) -> FinalFinding:
        """Creates or replaces the final finding of an AI finding."""
        ...

    async def list_for_run(self, analysis_run_id: UUID) -> list[FinalFinding]: ...


@dataclass(frozen=True, slots=True)
class HumanReviewEntry:
    ai_finding_id: UUID
    evaluation_id: UUID
    reviewer_id: UUID
    action: str
    comment: str | None
    previous_values: dict[str, str | None]
    new_values: dict[str, str | None]


@dataclass(frozen=True, slots=True)
class HumanReviewRecord:
    action: str
    comment: str | None
    reviewer_id: UUID
    created_at: datetime


class HumanReviewRepository(Protocol):
    async def add(self, entry: HumanReviewEntry) -> None: ...

    async def history(self, ai_finding_id: UUID) -> list[HumanReviewRecord]: ...
