from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from auditor.shared.domain.audit import AuditValue


@dataclass(frozen=True, slots=True)
class AuditLogEntry:
    id: UUID
    occurred_at: datetime
    action: str
    outcome: str
    actor_id: UUID | None
    actor_role: str | None
    company_id: UUID | None
    resource_type: str | None
    resource_id: UUID | None
    request_id: str | None
    details: dict[str, AuditValue]
