from __future__ import annotations

from uuid import UUID

from auditor.evaluations.application.access import EvaluationAccess
from auditor.evaluations.application.ports import (
    AnalysisRunRepository,
    ConsentRepository,
    NameDirectory,
)
from auditor.evaluations.application.views import EvaluationDetail
from auditor.evaluations.domain.consent import CURRENT_CONSENT
from auditor.evaluations.domain.progress import progress
from auditor.evaluations.domain.state_machine import Party, allowed_triggers
from auditor.identity.public import Permission
from auditor.shared.domain.actor import Actor, Role


def party_for(actor: Actor) -> Party | None:
    if actor.role is Role.SME:
        return Party.SME
    if actor.role in {Role.REVIEWER, Role.ADMIN}:
        return Party.REVIEWER
    return None


class GetEvaluation:
    def __init__(
        self,
        access: EvaluationAccess,
        runs: AnalysisRunRepository,
        consents: ConsentRepository,
        companies: NameDirectory,
        users: NameDirectory,
    ) -> None:
        self._access = access
        self._runs = runs
        self._consents = consents
        self._companies = companies
        self._users = users

    async def execute(self, actor: Actor, evaluation_id: UUID) -> EvaluationDetail:
        evaluation = await self._access.require(actor, evaluation_id, Permission.VIEW_EVALUATIONS)
        run = await self._runs.current(evaluation)
        consent_given = await self._consents.has_consent(
            evaluation.id, actor.user_id, CURRENT_CONSENT.version
        )
        companies = await self._companies.names_of([evaluation.company_id])
        reviewers = (
            await self._users.names_of([evaluation.reviewer_id]) if evaluation.reviewer_id else {}
        )
        party = party_for(actor)
        return EvaluationDetail(
            evaluation=evaluation,
            run=run,
            company_name=companies.get(evaluation.company_id),
            reviewer_name=reviewers.get(evaluation.reviewer_id) if evaluation.reviewer_id else None,
            consent_given=consent_given,
            progress=progress(evaluation.status, evaluation.failed_stage),
            available_triggers=allowed_triggers(evaluation.status, party) if party else set(),
        )
