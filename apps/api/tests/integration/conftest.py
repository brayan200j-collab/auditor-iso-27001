from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from auditor.shared.infrastructure.database import create_engine, create_session_factory
from tests.support.database import ensure_database, migrate, reset_schema, truncate_all
from tests.support.settings import test_database_url


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
