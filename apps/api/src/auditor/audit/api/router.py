from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from auditor.audit.application.list_audit_logs import AuditLogFilters, ListAuditLogs
from auditor.shared.api.dependencies import CurrentActor, use_case
from auditor.shared.api.pagination import PageParams
from auditor.shared.api.schemas import ERROR_RESPONSES, ApiModel, PageMeta, QueryModel
from auditor.shared.domain.audit import AuditAction, AuditOutcome

router = APIRouter(prefix="/api/v1", tags=["audit"], responses=ERROR_RESPONSES)


class AuditLogResponse(ApiModel):
    id: UUID
    occurred_at: datetime
    action: AuditAction
    outcome: AuditOutcome
    actor_id: UUID | None
    actor_role: str | None
    company_id: UUID | None
    resource_type: str | None
    resource_id: UUID | None
    request_id: str | None
    details: dict[str, Any]


class AuditLogPage(ApiModel):
    items: list[AuditLogResponse]
    meta: PageMeta


class AuditLogQuery(QueryModel):
    action: AuditAction | None = None
    outcome: AuditOutcome | None = None
    company_id: UUID | None = None
    since: datetime | None = None
    until: datetime | None = None


@router.get("/audit-logs", response_model=AuditLogPage, summary="Registro de auditoría")
async def list_audit_logs(
    actor: CurrentActor,
    page: PageParams,
    query: Annotated[AuditLogQuery, Query()],
    list_logs: Annotated[ListAuditLogs, Depends(use_case(ListAuditLogs))],
) -> AuditLogPage:
    result = await list_logs.execute(
        actor,
        AuditLogFilters(
            action=query.action,
            outcome=query.outcome,
            company_id=query.company_id,
            since=query.since,
            until=query.until,
        ),
        page,
    )
    return AuditLogPage(
        items=[
            AuditLogResponse(
                id=entry.id,
                occurred_at=entry.occurred_at,
                action=AuditAction(entry.action),
                outcome=AuditOutcome(entry.outcome),
                actor_id=entry.actor_id,
                actor_role=entry.actor_role,
                company_id=entry.company_id,
                resource_type=entry.resource_type,
                resource_id=entry.resource_id,
                request_id=entry.request_id,
                details=entry.details,
            )
            for entry in result.items
        ],
        meta=PageMeta(total=result.total, page=result.page, page_size=result.page_size),
    )
