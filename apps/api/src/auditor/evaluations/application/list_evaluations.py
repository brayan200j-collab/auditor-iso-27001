from __future__ import annotations

from auditor.evaluations.application.access import data_scope
from auditor.evaluations.application.ports import (
    EvaluationFilters,
    EvaluationRepository,
    NameDirectory,
)
from auditor.evaluations.application.views import EvaluationSummary
from auditor.identity.public import Permission
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.pagination import Page, PageRequest


class ListEvaluations:
    """Admins see all, reviewers their assignments, SMEs their own company (scope enforced)."""

    def __init__(
        self,
        evaluations: EvaluationRepository,
        companies: NameDirectory,
        users: NameDirectory,
    ) -> None:
        self._evaluations = evaluations
        self._companies = companies
        self._users = users

    async def execute(
        self, actor: Actor, filters: EvaluationFilters, page: PageRequest
    ) -> Page[EvaluationSummary]:
        scope = data_scope(actor, Permission.VIEW_EVALUATIONS)
        result = await self._evaluations.list(scope, filters, page)
        company_names = await self._companies.names_of({e.company_id for e in result.items})
        reviewer_ids = {e.reviewer_id for e in result.items if e.reviewer_id}
        reviewer_names = await self._users.names_of(reviewer_ids)
        return Page(
            items=[
                EvaluationSummary(
                    evaluation=evaluation,
                    company_name=company_names.get(evaluation.company_id),
                    reviewer_name=(
                        reviewer_names.get(evaluation.reviewer_id)
                        if evaluation.reviewer_id
                        else None
                    ),
                )
                for evaluation in result.items
            ],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )
