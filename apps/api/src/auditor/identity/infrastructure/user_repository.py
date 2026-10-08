from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.identity.application.ports import NewUser, UserFilters
from auditor.identity.domain.user import User
from auditor.identity.infrastructure.models import CompanyUserModel, UserModel
from auditor.shared.domain.actor import Role
from auditor.shared.domain.errors import ResourceNotFoundError
from auditor.shared.domain.pagination import Page, PageRequest
from auditor.shared.infrastructure.database import contains_pattern


def _base() -> Select[UserModel, UUID]:
    # Outer join: the company id column is NULL for users without a company.
    return select(UserModel, CompanyUserModel.company_id).outerjoin(
        CompanyUserModel, CompanyUserModel.user_id == UserModel.id
    )


def _to_user(model: UserModel, company_id: UUID | None) -> User:
    return User(
        id=model.id,
        email=model.email,
        full_name=model.full_name,
        role=Role(model.role),
        active=model.active,
        company_id=company_id,
        created_at=model.created_at,
    )


class SqlUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: UUID) -> User | None:
        row = (await self._session.execute(_base().where(UserModel.id == user_id))).first()
        return _to_user(row[0], row[1]) if row else None

    async def get_by_email(self, email: str) -> User | None:
        query = _base().where(func.lower(UserModel.email) == email.strip().lower())
        row = (await self._session.execute(query)).first()
        return _to_user(row[0], row[1]) if row else None

    async def list(self, filters: UserFilters, page: PageRequest) -> Page[User]:
        query = _base()
        if filters.role:
            query = query.where(UserModel.role == filters.role)
        if filters.company_id:
            query = query.where(CompanyUserModel.company_id == filters.company_id)
        if filters.search:
            pattern = contains_pattern(filters.search)
            query = query.where(
                or_(
                    func.lower(UserModel.email).like(pattern, escape="\\"),
                    func.lower(UserModel.full_name).like(pattern, escape="\\"),
                )
            )
        total = await self._session.scalar(select(func.count()).select_from(query.subquery()))
        rows = await self._session.execute(
            query.order_by(UserModel.created_at.desc()).offset(page.offset).limit(page.page_size)
        )
        items = [_to_user(model, company_id) for model, company_id in rows.all()]
        return Page(items=items, total=total or 0, page=page.page, page_size=page.page_size)

    async def names_of(self, ids: Iterable[UUID]) -> dict[UUID, str]:
        wanted = set(ids)
        if not wanted:
            return {}
        rows = await self._session.execute(
            select(UserModel.id, UserModel.full_name).where(UserModel.id.in_(wanted))
        )
        return dict(rows.all())

    async def is_active_reviewer(self, user_id: UUID) -> bool:
        role = await self._session.scalar(
            select(UserModel.role).where(UserModel.id == user_id, UserModel.active.is_(True))
        )
        return role == Role.REVIEWER

    async def add(self, user: NewUser) -> User:
        self._session.add(
            UserModel(
                id=user.id,
                email=user.email.strip().lower(),
                full_name=user.full_name,
                role=user.role,
            )
        )
        if user.company_id:
            await self._session.flush()
            self._session.add(CompanyUserModel(company_id=user.company_id, user_id=user.id))
        await self._session.flush()
        created = await self.get(user.id)
        if created is None:  # pragma: no cover - just inserted
            raise ResourceNotFoundError()
        return created

    async def update(
        self,
        user_id: UUID,
        *,
        full_name: str | None = None,
        active: bool | None = None,
        company_id: UUID | None = None,
    ) -> User:
        model = await self._session.get(UserModel, user_id)
        if model is None:
            raise ResourceNotFoundError()
        if full_name is not None:
            model.full_name = full_name
        if active is not None:
            model.active = active
        if company_id is not None:
            await self._session.execute(
                delete(CompanyUserModel).where(CompanyUserModel.user_id == user_id)
            )
            self._session.add(CompanyUserModel(company_id=company_id, user_id=user_id))
        model.updated_at = datetime.now(UTC)
        await self._session.flush()
        updated = await self.get(user_id)
        if updated is None:  # pragma: no cover - just updated
            raise ResourceNotFoundError()
        return updated
