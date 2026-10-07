"""Composition root: builds adapters and wires use cases. The only place that knows them all."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, cast

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from auditor.audit.application.list_audit_logs import ListAuditLogs
from auditor.audit.infrastructure.audit_log_reader import SqlAuditLogReader
from auditor.audit.infrastructure.sql_audit_logger import SqlAuditLogger
from auditor.companies.infrastructure.repository import SqlCompanyRepository
from auditor.config import Settings
from auditor.identity.application.get_profile import GetProfile
from auditor.identity.application.ports import TokenVerifier
from auditor.identity.application.record_session_event import RecordSessionEvent
from auditor.identity.application.resolve_actor import ResolveActor
from auditor.identity.infrastructure.token_verifiers import SupabaseJwtVerifier, TestJwtVerifier
from auditor.identity.infrastructure.user_repository import SqlUserRepository
from auditor.shared.domain.actor import Actor
from auditor.shared.infrastructure.database import (
    SessionUnitOfWork,
    SystemClock,
    create_engine,
    create_session_factory,
    ping,
)

Factory = Callable[["RequestScope"], Any]


def build_token_verifier(settings: Settings) -> TokenVerifier:
    if settings.auth_provider == "test":
        secret = settings.test_jwt_secret
        if secret is None:
            raise RuntimeError("TEST_JWT_SECRET is required for the test token verifier.")
        return TestJwtVerifier(
            secret.get_secret_value(), settings.supabase_jwt_issuer, settings.supabase_jwt_audience
        )
    jwks_url = settings.supabase_url.rstrip("/") + "/auth/v1/.well-known/jwks.json"
    return SupabaseJwtVerifier(
        jwks_url, settings.supabase_jwt_issuer, settings.supabase_jwt_audience
    )


@dataclass
class AppContainer:
    settings: Settings
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]
    token_verifier: TokenVerifier
    clock: SystemClock = field(default_factory=SystemClock)
    factories: dict[type[Any], Factory] = field(default_factory=dict)

    @classmethod
    def build(cls, settings: Settings) -> AppContainer:
        engine = create_engine(
            settings.database_url,
            pool_size=settings.database_pool_size,
            use_null_pool=settings.app_env == "test",
        )
        return cls(
            settings=settings,
            engine=engine,
            session_factory=create_session_factory(engine),
            token_verifier=build_token_verifier(settings),
            factories=build_factories(),
        )

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
    """Per-request (or per-job) object graph bound to one database session."""

    container: AppContainer
    session: AsyncSession

    @property
    def settings(self) -> Settings:
        return self.container.settings

    @cached_property
    def uow(self) -> SessionUnitOfWork:
        return SessionUnitOfWork(self.session)

    @cached_property
    def audit(self) -> SqlAuditLogger:
        return SqlAuditLogger(self.session, self.container.session_factory)

    @cached_property
    def users(self) -> SqlUserRepository:
        return SqlUserRepository(self.session)

    @cached_property
    def companies(self) -> SqlCompanyRepository:
        return SqlCompanyRepository(self.session)

    def resolve[T](self, use_case: type[T]) -> T:
        factory = self.container.factories.get(use_case)
        if factory is None:
            raise LookupError(f"No factory registered for {use_case.__name__}")
        return cast(T, factory(self))

    async def resolve_actor(self, bearer_token: str | None) -> Actor:
        return await ResolveActor(self.container.token_verifier, self.users).execute(bearer_token)


def build_factories() -> dict[type[Any], Factory]:
    return {
        GetProfile: lambda s: GetProfile(s.users, s.companies),
        RecordSessionEvent: lambda s: RecordSessionEvent(s.audit),
        ListAuditLogs: lambda s: ListAuditLogs(SqlAuditLogReader(s.session)),
    }
