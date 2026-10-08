"""Dependency injection seam between routers and the composition root.

Routers only depend on application use cases. `get_resolver` is a placeholder that the
composition root (`auditor.main`) replaces with a request-scoped resolver through
`app.dependency_overrides`, so the API layer never imports infrastructure.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from typing import Annotated, Protocol

from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auditor.shared.domain.actor import Actor


class UseCaseResolver(Protocol):
    def resolve[T](self, use_case: type[T]) -> T: ...

    async def resolve_actor(self, bearer_token: str | None) -> Actor: ...


async def get_resolver() -> AsyncIterator[UseCaseResolver]:  # pragma: no cover - always overridden
    raise RuntimeError("The use case resolver has not been wired.")
    yield


Resolver = Annotated[UseCaseResolver, Depends(get_resolver)]


def use_case[T](use_case_type: type[T]) -> Callable[[UseCaseResolver], T]:
    def dependency(resolver: Resolver) -> T:
        return resolver.resolve(use_case_type)

    return dependency


_bearer_scheme = HTTPBearer(auto_error=False, description="Supabase access token (JWT)")


async def current_actor(
    resolver: Resolver,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(_bearer_scheme)],
) -> Actor:
    token = credentials.credentials.strip() if credentials else None
    return await resolver.resolve_actor(token or None)


CurrentActor = Annotated[Actor, Depends(current_actor)]
