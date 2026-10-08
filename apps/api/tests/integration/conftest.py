from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from auditor.config import Settings
from auditor.main import create_app
from auditor.shared.infrastructure.database import create_engine, create_session_factory
from tests.support.database import ensure_database, migrate, reset_schema, truncate_all
from tests.support.fakes import FakeAuthAdmin
from tests.support.settings import make_settings, test_database_url


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if "tests/integration" in str(item.path).replace("\\", "/"):
            item.add_marker(pytest.mark.integration)


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    url = test_database_url()
    ensure_database(url)
    reset_schema(url)
    migrate(url)
    yield url


@pytest.fixture(scope="session")
async def engine(database_url: str) -> AsyncIterator[AsyncEngine]:
    engine = create_engine(database_url, use_null_pool=True)
    yield engine
    await engine.dispose()


@pytest.fixture(autouse=True)
async def _clean_database(engine: AsyncEngine) -> AsyncIterator[None]:
    await truncate_all(engine)
    yield


@pytest.fixture
async def session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with create_session_factory(engine)() as session:
        yield session


@pytest.fixture
def settings(database_url: str, tmp_path: Path) -> Settings:
    return make_settings(tmp_storage=tmp_path / "storage", database_url=database_url)


@pytest.fixture
def auth_admin() -> FakeAuthAdmin:
    return FakeAuthAdmin()


@pytest.fixture
def app(settings: Settings, auth_admin: FakeAuthAdmin) -> FastAPI:
    application = create_app(settings)
    application.state.container.auth_admin = auth_admin
    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    # Background jobs (e.g. the report queued on approval) must finish before the next test
    # truncates the tables.
    await app.state.container.runner.drain()
