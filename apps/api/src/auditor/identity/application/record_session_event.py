from __future__ import annotations

from auditor.shared.application.ports import AuditLogger
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.audit import AuditAction, AuditEntry


class RecordSessionEvent:
    """Records login/logout in the audit trail (authentication itself happens in Supabase Auth)."""

    def __init__(self, audit: AuditLogger) -> None:
        self._audit = audit

    async def execute(self, actor: Actor, action: AuditAction) -> None:
        if action not in {AuditAction.LOGIN, AuditAction.LOGOUT}:
            raise ValueError("only LOGIN and LOGOUT are session events")
        await self._audit.record_immediately(
            AuditEntry(
                action=action,
                actor_id=actor.user_id,
                actor_role=actor.role,
                company_id=actor.company_id,
                resource_type="user",
                resource_id=actor.user_id,
            )
        )
