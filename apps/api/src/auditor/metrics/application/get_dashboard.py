from __future__ import annotations

from auditor.identity.public import Permission, authorize
from auditor.metrics.application.ports import DashboardScope, MetricsReader
from auditor.metrics.domain.metrics import DashboardCounts
from auditor.shared.domain.actor import Actor, Role


class GetDashboard:
    def __init__(self, reader: MetricsReader) -> None:
        self._reader = reader

    async def execute(self, actor: Actor) -> DashboardCounts:
        authorize(actor, Permission.VIEW_EVALUATIONS)
        if actor.role is Role.SME:
            scope = DashboardScope(company_id=actor.company_id)
        elif actor.role is Role.REVIEWER:
            scope = DashboardScope(reviewer_id=actor.user_id)
        else:
            scope = DashboardScope()
        return await self._reader.dashboard(scope)
