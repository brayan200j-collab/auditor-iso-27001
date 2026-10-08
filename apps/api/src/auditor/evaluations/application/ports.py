from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from auditor.evaluations.domain.evaluation import AnalysisRun, Evaluation
from auditor.evaluations.domain.scope import DataScope
from auditor.evaluations.domain.status import EvaluationStatus
from auditor.shared.domain.pagination import Page, PageRequest


@dataclass(frozen=True, slots=True)
class NewEvaluation:
    company_id: UUID
    created_by: UUID
    title: str


@dataclass(frozen=True, slots=True)
class EvaluationFilters:
    status: EvaluationStatus | None = None
    company_id: UUID | None = None


class EvaluationRepository(Protocol):
    async def add(self, evaluation: NewEvaluation) -> Evaluation: ...

    async def get(self, evaluation_id: UUID, scope: DataScope) -> Evaluation | None: ...

    async def exists(self, evaluation_id: UUID) -> bool:
        """Unscoped existence check, used only to audit denied access attempts."""
        ...

    async def list(
        self, scope: DataScope, filters: EvaluationFilters, page: PageRequest
    ) -> Page[Evaluation]: ...

    async def count_for_company(self, company_id: UUID) -> int: ...

    async def save(self, evaluation: Evaluation, expected_status: EvaluationStatus) -> None:
        """Persists changes only if the stored status is still `expected_status`."""
        ...

    async def set_reviewer(self, evaluation_id: UUID, reviewer_id: UUID) -> None: ...

    async def lock(self, evaluation_id: UUID) -> None:
        """Row lock for the rest of the transaction (serializes concurrent changes)."""
        ...


class AnalysisRunRepository(Protocol):
    async def add(self, evaluation_id: UUID, run_number: int) -> AnalysisRun: ...

    async def current(self, evaluation: Evaluation) -> AnalysisRun: ...

    async def get(self, run_id: UUID) -> AnalysisRun | None: ...

    async def bind_checklist(self, run_id: UUID, checklist_version_id: UUID) -> None: ...

    async def mark_started(self, run_id: UUID) -> None: ...

    async def mark_finished(self, run_id: UUID) -> None: ...


class ConsentRepository(Protocol):
    async def has_consent(self, evaluation_id: UUID, user_id: UUID, version: str) -> bool: ...

    async def add(self, evaluation_id: UUID, user_id: UUID, version: str, sha256: str) -> None: ...


class NameDirectory(Protocol):
    """Display names of companies or users, provided by the owning module."""

    async def names_of(self, ids: Iterable[UUID]) -> dict[UUID, str]: ...


class ReviewerDirectory(Protocol):
    async def is_active_reviewer(self, user_id: UUID) -> bool: ...


class AnalysisProgressReader(Protocol):
    async def progress(self, run: AnalysisRun) -> tuple[int, int] | None:
        """(criteria with a finding, active criteria of the bound checklist), if known."""
        ...
