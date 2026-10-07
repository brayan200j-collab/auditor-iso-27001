"""Composition root: builds adapters and wires use cases. The only place that knows them all."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, cast

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from auditor.config import Settings
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.errors import UnauthorizedError
from auditor.shared.infrastructure.database import (
    SystemClock,
    create_engine,
    create_session_factory,
    ping,
)

Factory = Callable[["RequestScope"], Any]


@dataclass
class AppContainer:
    settings: Settings
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]
    clock: SystemClock = field(default_factory=SystemClock)
    factories: dict[type[Any], Factory] = field(default_factory=dict)

    @classmethod
    def build(cls, settings: Settings) -> AppContainer:
        engine = create_engine(
            settings.database_url,
            pool_size=settings.database_pool_size,
            use_null_pool=settings.app_env == "test",
        )
        container = cls(
            settings=settings, engine=engine, session_factory=create_session_factory(engine)
        )
        container.factories = build_factories()
        return container

    async def is_ready(self) -> bool:
        return await ping(self.engine)

    async def aclose(self) -> None:
        await self.engine.dispose()

    @asynccontextmanager
    async def scope(self) -> AsyncIterator[RequestScope]:
        async with self.session_factory() as session:
            yield RequestScope(container=self, session=session)

    async def request_resolver(self) -> AsyncIterator[RequestScope]:
        async with self.scope() as scope:
            yield scope


@dataclass
class RequestScope:
    container: AppContainer
    session: AsyncSession

    @property
    def settings(self) -> Settings:
        return self.container.settings

    def resolve[T](self, use_case: type[T]) -> T:
        factory = self.container.factories.get(use_case)
        if factory is None:
            raise LookupError(f"No factory registered for {use_case.__name__}")
        return cast(T, factory(self))

    async def resolve_actor(self, bearer_token: str | None) -> Actor:
        raise UnauthorizedError(detail="identity module not wired")


def build_factories() -> dict[type[Any], Factory]:
    return {}
