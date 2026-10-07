from __future__ import annotations

from collections.abc import Callable

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.audit.infrastructure.models import AuditLogModel
from auditor.shared.domain.audit import AuditEntry

SessionFactory = Callable[[], AsyncSession]


def _request_id() -> str | None:
    value = structlog.contextvars.get_contextvars().get("request_id")
    return value if isinstance(value, str) else None


def _model(entry: AuditEntry) -> AuditLogModel:
    return AuditLogModel(
        action=entry.action,
        outcome=entry.outcome,
        actor_id=entry.actor_id,
        actor_role=entry.actor_role,
        company_id=entry.company_id,
        resource_type=entry.resource_type,
        resource_id=entry.resource_id,
        request_id=_request_id(),
        details=dict(entry.details),
    )


class SqlAuditLogger:
    def __init__(self, session: AsyncSession, session_factory: SessionFactory) -> None:
        self._session = session
        self._session_factory = session_factory

    async def record(self, entry: AuditEntry) -> None:
        self._session.add(_model(entry))

    async def record_immediately(self, entry: AuditEntry) -> None:
        async with self._session_factory() as session:
            session.add(_model(entry))
            await session.commit()
