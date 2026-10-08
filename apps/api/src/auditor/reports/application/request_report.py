from __future__ import annotations

from uuid import UUID

from auditor.evaluations.public import EvaluationAccess, EvaluationStatus
from auditor.identity.public import Permission
from auditor.reports.application.schedule_report import ScheduleReport
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.errors import ConflictError


class ReportNeedsApprovalError(ConflictError):
    default_message = "El informe solo se puede generar después de aprobar la evaluación."


class RequestReport:
    """Reviewer/admin action, e.g. after the automatic generation failed (idempotent per run)."""

    def __init__(self, access: EvaluationAccess, schedule: ScheduleReport) -> None:
        self._access = access
        self._schedule = schedule

    async def execute(self, actor: Actor, evaluation_id: UUID) -> None:
        evaluation = await self._access.require(actor, evaluation_id, Permission.GENERATE_REPORT)
        if evaluation.status is not EvaluationStatus.APPROVED:
            raise ReportNeedsApprovalError()
        await self._schedule.execute(evaluation, actor.user_id)
