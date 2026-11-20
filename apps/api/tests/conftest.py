from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr

from clarity_api.app import create_app
from clarity_api.queue import RecordingQueue
from clarity_api.security import hash_password
from clarity_api.settings import Settings
from clarity_persistence.testing import database_url_for_tests, recreate_tables

PASSWORD = "correct horse battery staple"
PASSWORD_HASH = hash_password(PASSWORD)


@pytest.fixture
async def settings(tmp_path: Path) -> Settings:
    url = database_url_for_tests()
    if not url:
        pytest.skip("CLARITY_TEST_DATABASE_URL is not configured")
    await recreate_tables(url)
    return Settings(
        database_url=url,
        secret_key=SecretStr("test-secret"),
        credentials_key=SecretStr("test-credentials"),
        admin_username="admin",
        admin_password_hash=SecretStr(PASSWORD_HASH),
        artifact_dir=tmp_path / "artifacts",
        secure_cookies=False,
        _env_file=None,
    )


@pytest.fixture
def password() -> str:
    return PASSWORD


@pytest.fixture
def queue() -> RecordingQueue:
    return RecordingQueue()


@pytest.fixture
async def app(settings: Settings, queue: RecordingQueue) -> AsyncIterator[FastAPI]:
    application = create_app(settings, queue)
    async with application.router.lifespan_context(application):
        yield application


@pytest.fixture
async def anonymous(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
async def client(anonymous: AsyncClient) -> AsyncClient:
    response = await anonymous.post(
        "/api/auth/login", json={"username": "admin", "password": PASSWORD}
    )
    assert response.status_code == 204
    return anonymous
