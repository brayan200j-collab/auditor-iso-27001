from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from auditor.identity.application.ports import AuthAdmin, CompanyDirectory, UserRepository
from auditor.identity.domain.permissions import Permission, authorize
from auditor.identity.domain.rules import check_company_for_role, normalize_full_name
from auditor.identity.domain.user import User
from auditor.shared.application.ports import AuditLogger, UnitOfWork
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.audit import AuditAction, AuditEntry
from auditor.shared.domain.errors import (
    ConflictError,
    ResourceNotFoundError,
    ValidationFailedError,
)


@dataclass(frozen=True, slots=True)
class UpdateUserInput:
    full_name: str | None = None
    active: bool | None = None
    company_id: UUID | None = None


class UpdateUser:
    """Edits a profile. Deactivation also blocks sign-in at the identity provider."""

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

    async def execute(self, actor: Actor, user_id: UUID, data: UpdateUserInput) -> User:
        authorize(actor, Permission.MANAGE_USERS)
        current = await self._users.get(user_id)
        if current is None:
            raise ResourceNotFoundError()
        if data.active is False and user_id == actor.user_id:
            raise ConflictError("No puedes desactivar tu propia cuenta.")
        if data.company_id is not None:
            check_company_for_role(current.role, data.company_id)
            if not await self._companies.exists(data.company_id):
                raise ValidationFailedError("La empresa seleccionada no existe.")

        updated = await self._users.update(
            user_id,
            full_name=normalize_full_name(data.full_name) if data.full_name else None,
            active=data.active,
            company_id=data.company_id,
        )
        if data.active is not None and data.active != current.active:
            await self._auth_admin.set_banned(user_id, banned=not data.active)
        await self._audit.record(
            AuditEntry(
                action=AuditAction.USER_UPDATED,
                actor_id=actor.user_id,
                actor_role=actor.role,
                company_id=updated.company_id,
                resource_type="user",
                resource_id=user_id,
                details={"active": updated.active},
            )
        )
        await self._uow.commit()
        return updated
