from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import Field

from auditor.identity.application.create_user import CreateUser, CreateUserInput
from auditor.identity.application.get_user import GetUser
from auditor.identity.application.list_users import ListUsers
from auditor.identity.application.ports import UserFilters
from auditor.identity.application.update_user import UpdateUser, UpdateUserInput
from auditor.identity.domain.user import User
from auditor.shared.api.dependencies import CurrentActor, use_case
from auditor.shared.api.pagination import PageParams
from auditor.shared.api.schemas import ERROR_RESPONSES, ApiModel, PageMeta, RequestModel
from auditor.shared.domain.actor import Role

# Pragmatic syntax check; deliverability is proven by the Supabase invitation email.
EMAIL_PATTERN = r"^[^@\s]{1,64}@[^@\s]+\.[^@\s]{2,}$"

router = APIRouter(prefix="/api/v1/users", tags=["users"], responses=ERROR_RESPONSES)


class UserCreateRequest(RequestModel):
    email: str = Field(max_length=320, pattern=EMAIL_PATTERN)
    full_name: str = Field(min_length=2, max_length=200)
    role: Role
    company_id: UUID | None = None


class UserUpdateRequest(RequestModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=200)
    active: bool | None = None
    company_id: UUID | None = None


class UserResponse(ApiModel):
    id: UUID
    email: str
    full_name: str
    role: Role
    active: bool
    company_id: UUID | None
    created_at: datetime

    @classmethod
    def of(cls, user: User) -> UserResponse:
        return cls(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            active=user.active,
            company_id=user.company_id,
            created_at=user.created_at,
        )


class UserPage(ApiModel):
    items: list[UserResponse]
    meta: PageMeta


def user_filters(
    role: Annotated[Role | None, Query(description="Filtrar por rol")] = None,
    company_id: Annotated[UUID | None, Query(description="Filtrar por empresa")] = None,
    search: Annotated[str | None, Query(max_length=100, description="Correo o nombre")] = None,
) -> UserFilters:
    return UserFilters(role=role, company_id=company_id, search=search)


@router.get("", response_model=UserPage, summary="Listar usuarios")
async def list_users(
    actor: CurrentActor,
    page: PageParams,
    filters: Annotated[UserFilters, Depends(user_filters)],
    list_use_case: Annotated[ListUsers, Depends(use_case(ListUsers))],
) -> UserPage:
    result = await list_use_case.execute(actor, filters, page)
    return UserPage(
        items=[UserResponse.of(user) for user in result.items],
        meta=PageMeta(total=result.total, page=result.page, page_size=result.page_size),
    )


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario e invitarlo por correo",
)
async def create_user(
    actor: CurrentActor,
    body: UserCreateRequest,
    create: Annotated[CreateUser, Depends(use_case(CreateUser))],
) -> UserResponse:
    user = await create.execute(
        actor,
        CreateUserInput(
            email=body.email,
            full_name=body.full_name,
            role=body.role,
            company_id=body.company_id,
        ),
    )
    return UserResponse.of(user)


@router.get("/{user_id}", response_model=UserResponse, summary="Detalle de usuario")
async def get_user(
    actor: CurrentActor,
    user_id: UUID,
    get: Annotated[GetUser, Depends(use_case(GetUser))],
) -> UserResponse:
    return UserResponse.of(await get.execute(actor, user_id))


@router.patch("/{user_id}", response_model=UserResponse, summary="Actualizar usuario")
async def update_user(
    actor: CurrentActor,
    user_id: UUID,
    body: UserUpdateRequest,
    update: Annotated[UpdateUser, Depends(use_case(UpdateUser))],
) -> UserResponse:
    user = await update.execute(
        actor,
        user_id,
        UpdateUserInput(full_name=body.full_name, active=body.active, company_id=body.company_id),
    )
    return UserResponse.of(user)
