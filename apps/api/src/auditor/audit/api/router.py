from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from auditor.audit.application.list_audit_logs import AuditLogFilters, ListAuditLogs
from auditor.shared.api.dependencies import CurrentActor, use_case
from auditor.shared.api.pagination import PageParams
from auditor.shared.api.schemas import ERROR_RESPONSES, ApiModel, PageMeta
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


def audit_filters(
    action: Annotated[AuditAction | None, Query()] = None,
    outcome: Annotated[AuditOutcome | None, Query()] = None,
    company_id: Annotated[UUID | None, Query()] = None,
    since: Annotated[datetime | None, Query()] = None,
    until: Annotated[datetime | None, Query()] = None,
) -> AuditLogFilters:
    return AuditLogFilters(
        action=action, outcome=outcome, company_id=company_id, since=since, until=until
    )


@router.get("/audit-logs", response_model=AuditLogPage, summary="Registro de auditoría")
async def list_audit_logs(
    actor: CurrentActor,
    page: PageParams,
    filters: Annotated[AuditLogFilters, Depends(audit_filters)],
    list_logs: Annotated[ListAuditLogs, Depends(use_case(ListAuditLogs))],
) -> AuditLogPage:
    result = await list_logs.execute(actor, filters, page)
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
