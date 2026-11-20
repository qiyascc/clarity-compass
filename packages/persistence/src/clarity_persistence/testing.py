import os
from pathlib import Path

from clarity_persistence.database import create_engine
from clarity_persistence.models import Base

ENV_FILE = Path(__file__).resolve().parents[4] / ".env"


def database_url_for_tests() -> str | None:
    if url := os.environ.get("CLARITY_TEST_DATABASE_URL"):
        return url
    if ENV_FILE.is_file():
        for line in ENV_FILE.read_text().splitlines():
            key, _, value = line.partition("=")
            if key.strip() == "CLARITY_TEST_DATABASE_URL":
                return value.strip()
    return None


async def recreate_tables(url: str) -> None:
    engine = create_engine(url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()
