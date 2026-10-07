from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from auditor.identity.application.get_profile import GetProfile
from auditor.identity.application.record_session_event import RecordSessionEvent
from auditor.shared.api.dependencies import CurrentActor, use_case
from auditor.shared.api.schemas import ERROR_RESPONSES, ApiModel
from auditor.shared.domain.actor import Role
from auditor.shared.domain.audit import AuditAction

router = APIRouter(prefix="/api/v1", tags=["identity"], responses=ERROR_RESPONSES)


class ProfileResponse(ApiModel):
    id: UUID
    email: str
    full_name: str
    role: Role
    company_id: UUID | None
    company_name: str | None


@router.get("/me", response_model=ProfileResponse, summary="Usuario autenticado")
async def me(
    actor: CurrentActor, get_profile: Annotated[GetProfile, Depends(use_case(GetProfile))]
) -> ProfileResponse:
    profile = await get_profile.execute(actor)
    return ProfileResponse(
        id=profile.id,
        email=profile.email,
        full_name=profile.full_name,
        role=profile.role,
        company_id=profile.company_id,
        company_name=profile.company_name,
    )


@router.post(
    "/auth/login-event",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Registra el inicio de sesión en la auditoría",
)
async def login_event(
    actor: CurrentActor,
    record: Annotated[RecordSessionEvent, Depends(use_case(RecordSessionEvent))],
) -> None:
    await record.execute(actor, AuditAction.LOGIN)


@router.post(
    "/auth/logout-event",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Registra el cierre de sesión en la auditoría",
)
async def logout_event(
    actor: CurrentActor,
    record: Annotated[RecordSessionEvent, Depends(use_case(RecordSessionEvent))],
) -> None:
    await record.execute(actor, AuditAction.LOGOUT)
