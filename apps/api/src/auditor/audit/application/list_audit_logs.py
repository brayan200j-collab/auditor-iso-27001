from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from auditor.audit.domain.log_entry import AuditLogEntry
from auditor.identity.public import Permission, authorize
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.audit import AuditAction, AuditOutcome
from auditor.shared.domain.pagination import Page, PageRequest


@dataclass(frozen=True, slots=True)
class AuditLogFilters:
    action: AuditAction | None = None
    outcome: AuditOutcome | None = None
    company_id: UUID | None = None
    actor_id: UUID | None = None
    since: datetime | None = None
    until: datetime | None = None


class AuditLogReader(Protocol):
    async def list(self, filters: AuditLogFilters, page: PageRequest) -> Page[AuditLogEntry]: ...


class ListAuditLogs:
    def __init__(self, reader: AuditLogReader) -> None:
        self._reader = reader

    async def execute(
        self, actor: Actor, filters: AuditLogFilters, page: PageRequest
    ) -> Page[AuditLogEntry]:
        authorize(actor, Permission.VIEW_AUDIT_LOGS)
        return await self._reader.list(filters, page)
