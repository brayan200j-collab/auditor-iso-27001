from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, MetaData, func, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.pool import NullPool

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def create_engine(
    database_url: str, *, pool_size: int = 5, use_null_pool: bool = False
) -> AsyncEngine:
    if use_null_pool:
        return create_async_engine(database_url, poolclass=NullPool)
    return create_async_engine(
        database_url, pool_size=pool_size, max_overflow=pool_size, pool_pre_ping=True
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


async def ping(engine: AsyncEngine) -> bool:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
    return True


class SessionUnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


def enum_check(column: str, values: type[StrEnum] | tuple[str, ...], name: str) -> CheckConstraint:
    """CHECK constraint restricting a text column to the given enum values."""
    allowed = tuple(item.value for item in values) if isinstance(values, type) else values
    quoted = ", ".join(f"'{value}'" for value in allowed)
    return CheckConstraint(f"{column} IN ({quoted})", name=name)


def utc_now_column() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
