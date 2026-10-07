from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.audit.application.list_audit_logs import AuditLogFilters
from auditor.audit.domain.log_entry import AuditLogEntry
from auditor.audit.infrastructure.models import AuditLogModel
from auditor.shared.domain.pagination import Page, PageRequest


class SqlAuditLogReader:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, filters: AuditLogFilters, page: PageRequest) -> Page[AuditLogEntry]:
        query = select(AuditLogModel)
        if filters.action:
            query = query.where(AuditLogModel.action == filters.action)
        if filters.outcome:
            query = query.where(AuditLogModel.outcome == filters.outcome)
        if filters.company_id:
            query = query.where(AuditLogModel.company_id == filters.company_id)
        if filters.actor_id:
            query = query.where(AuditLogModel.actor_id == filters.actor_id)
        if filters.since:
            query = query.where(AuditLogModel.occurred_at >= filters.since)
        if filters.until:
            query = query.where(AuditLogModel.occurred_at <= filters.until)
        total = await self._session.scalar(select(func.count()).select_from(query.subquery()))
        models = await self._session.scalars(
            query.order_by(AuditLogModel.occurred_at.desc())
            .offset(page.offset)
            .limit(page.page_size)
        )
        items = [
            AuditLogEntry(
                id=model.id,
                occurred_at=model.occurred_at,
                action=model.action,
                outcome=model.outcome,
                actor_id=model.actor_id,
                actor_role=model.actor_role,
                company_id=model.company_id,
                resource_type=model.resource_type,
                resource_id=model.resource_id,
                request_id=model.request_id,
                details=dict(model.details),
            )
            for model in models
        ]
        return Page(items=items, total=total or 0, page=page.page, page_size=page.page_size)
