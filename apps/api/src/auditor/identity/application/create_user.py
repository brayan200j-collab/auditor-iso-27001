from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from auditor.identity.application.ports import (
    AuthAdmin,
    CompanyDirectory,
    NewUser,
    UserRepository,
)
from auditor.identity.domain.permissions import Permission, authorize
from auditor.identity.domain.rules import check_company_for_role, normalize_full_name
from auditor.identity.domain.user import User
from auditor.shared.application.ports import AuditLogger, UnitOfWork
from auditor.shared.domain.actor import Actor, Role
from auditor.shared.domain.audit import AuditAction, AuditEntry
from auditor.shared.domain.errors import ConflictError, ValidationFailedError


@dataclass(frozen=True, slots=True)
class CreateUserInput:
    email: str
    full_name: str
    role: Role
    company_id: UUID | None


class CreateUser:
    """Creates the profile and invites the person through Supabase Auth to set a password.

    If the profile cannot be stored, an account invited by this call is deleted again so no
    orphan identity remains.
    """

    def __init__(
        self,
        users: UserRepository,
        auth_admin: AuthAdmin,
        companies: CompanyDirectory,
        audit: AuditLogger,
        uow: UnitOfWork,
    ) -> None:
        self._users = users
        self._auth_admin = auth_admin
        self._companies = companies
        self._audit = audit
        self._uow = uow

    async def execute(self, actor: Actor, data: CreateUserInput) -> User:
        authorize(actor, Permission.MANAGE_USERS)
        email = data.email.strip().lower()
        full_name = normalize_full_name(data.full_name)
        check_company_for_role(data.role, data.company_id)
        if data.company_id and not await self._companies.exists(data.company_id):
            raise ValidationFailedError("La empresa seleccionada no existe.")
        if await self._users.get_by_email(email):
            raise ConflictError("Ya existe un usuario con ese correo.")

        user_id, invited = await self._provision_account(email)
        try:
            user = await self._users.add(
                NewUser(
                    id=user_id,
                    email=email,
                    full_name=full_name,
                    role=data.role,
                    company_id=data.company_id,
                )
            )
            await self._audit.record(
                AuditEntry(
                    action=AuditAction.USER_CREATED,
                    actor_id=actor.user_id,
                    actor_role=actor.role,
                    company_id=data.company_id,
                    resource_type="user",
                    resource_id=user_id,
                    details={"role": data.role.value, "invited": invited},
                )
            )
            await self._uow.commit()
        except Exception:
            await self._uow.rollback()
            if invited:
                await self._auth_admin.delete_user(user_id)
            raise
        return user

    async def _provision_account(self, email: str) -> tuple[UUID, bool]:
        existing = await self._auth_admin.find_user_id(email)
        if existing is not None:
            return existing, False
        return await self._auth_admin.invite_user(email, redirect_to=None), True
