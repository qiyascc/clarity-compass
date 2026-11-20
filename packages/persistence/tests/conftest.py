from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from clarity_persistence.database import create_engine
from clarity_persistence.testing import database_url_for_tests, recreate_tables


@pytest.fixture(scope="session")
def database_url() -> str:
    url = database_url_for_tests()
    if not url:
        pytest.skip("CLARITY_TEST_DATABASE_URL is not configured")
    return url


@pytest.fixture
async def engine(database_url: str) -> AsyncIterator[AsyncEngine]:
    await recreate_tables(database_url)
    engine = create_engine(database_url)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
