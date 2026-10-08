from __future__ import annotations

from auditor.identity.public import Permission, authorize
from auditor.metrics.application.ports import MetricsReader
from auditor.metrics.domain.metrics import PilotMetrics, technical_metrics, value_metrics
from auditor.shared.domain.actor import Actor, Role


class GetPilotMetrics:
    """Admin and mentor share the same aggregate view; it never identifies companies or users."""

    def __init__(self, reader: MetricsReader) -> None:
        self._reader = reader

    async def execute(self, actor: Actor) -> PilotMetrics:
        authorize(actor, Permission.VIEW_ANONYMIZED_METRICS)
        return PilotMetrics(
            technical=technical_metrics(await self._reader.technical_totals()),
            value=value_metrics(await self._reader.survey_totals()),
            anonymized=actor.role is not Role.ADMIN,
        )
