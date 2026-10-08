from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from auditor.shared.domain.audit import AuditAction, AuditOutcome
from auditor.shared.infrastructure.database import Base, enum_check, utc_now_column


class AuditLogModel(Base):
    """Insert-only audit trail (a trigger rejects UPDATE and DELETE). No sensitive content.

    `actor_id` and `company_id` intentionally have no foreign keys so the trail survives deletions.
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        enum_check("action", AuditAction, "action_valid"),
        enum_check("outcome", AuditOutcome, "outcome_valid"),
        Index("ix_audit_logs_occurred_at", "occurred_at"),
        Index("ix_audit_logs_company_id", "company_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    occurred_at: Mapped[datetime] = utc_now_column()
    action: Mapped[str] = mapped_column(String(40))
    outcome: Mapped[str] = mapped_column(String(10))
    actor_id: Mapped[UUID | None] = mapped_column()
    actor_role: Mapped[str | None] = mapped_column(String(20))
    company_id: Mapped[UUID | None] = mapped_column()
    resource_type: Mapped[str | None] = mapped_column(String(40))
    resource_id: Mapped[UUID | None] = mapped_column()
    request_id: Mapped[str | None] = mapped_column(String(64))
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
