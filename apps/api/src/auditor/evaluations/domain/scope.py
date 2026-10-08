"""Data scope applied to every evaluation query (CLAUDE.md section 8, point 3).

Repositories receive a scope explicitly; there is no way to query evaluations without one.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AllEvaluations:
    """Administrators only."""


@dataclass(frozen=True, slots=True)
class CompanyEvaluations:
    company_id: UUID


@dataclass(frozen=True, slots=True)
class AssignedEvaluations:
    reviewer_id: UUID


DataScope = AllEvaluations | CompanyEvaluations | AssignedEvaluations
