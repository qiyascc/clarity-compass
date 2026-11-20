import os
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
from clarity_persistence.database import create_engine
from clarity_persistence.models import Base

PASSWORD = "correct horse battery staple"
PASSWORD_HASH = hash_password(PASSWORD)


def _database_url() -> str | None:
    if url := os.environ.get("CLARITY_TEST_DATABASE_URL"):
        return url
    env_file = Path(__file__).resolve().parents[3] / ".env"
    if env_file.is_file():
        for line in env_file.read_text().splitlines():
            key, _, value = line.partition("=")
            if key.strip() == "CLARITY_TEST_DATABASE_URL":
                return value.strip()
    return None


@pytest.fixture
async def settings(tmp_path: Path) -> Settings:
    url = _database_url()
    if not url:
        pytest.skip("CLARITY_TEST_DATABASE_URL is not configured")
    engine = create_engine(url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()
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
