"""Retention policy (CLAUDE.md sections 4 and 9).

Original PDFs and their text fragments are deleted `retention_days` after the evaluation is
approved. Final findings, the report and the audit trail are kept.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID


def purge_cutoff(now: datetime, retention_days: int) -> datetime:
    """Evaluations approved before this instant are due for purging."""
    if retention_days < 1:
        raise ValueError("retention_days must be at least 1")
    return now - timedelta(days=retention_days)


def purge_date(approved_at: datetime, retention_days: int) -> datetime:
    return approved_at + timedelta(days=retention_days)


@dataclass(frozen=True, slots=True)
class ExpiredDocument:
    id: UUID
    evaluation_id: UUID
    company_id: UUID
    storage_path: str | None


@dataclass(frozen=True, slots=True)
class PurgeSummary:
    evaluations: int
    documents: int
