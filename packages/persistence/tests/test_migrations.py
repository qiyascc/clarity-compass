import asyncio
from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import Connection, text

from clarity_persistence.database import create_engine, owned_by_application
from clarity_persistence.models import Base

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


async def _reset(url: str) -> None:
    engine = create_engine(url)
    async with engine.begin() as connection:
        await connection.execute(text("drop schema public cascade"))
        await connection.execute(text("create schema public"))
    await engine.dispose()


def _diff(connection: Connection) -> list[object]:
    context = MigrationContext.configure(connection, opts={"include_name": owned_by_application})
    return list(compare_metadata(context, Base.metadata))


async def _schema_diff(url: str) -> list[object]:
    engine = create_engine(url)
    async with engine.connect() as connection:
        diff = await connection.run_sync(_diff)
    await engine.dispose()
    return diff


async def _tables(url: str) -> set[str]:
    engine = create_engine(url)
    async with engine.connect() as connection:
        rows = await connection.execute(
            text("select tablename from pg_tables where schemaname = 'public'")
        )
        names = {row[0] for row in rows} - {"alembic_version"}
    await engine.dispose()
    return names


def test_migrations_match_the_models(database_url: str) -> None:
    asyncio.run(_reset(database_url))
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(config, "head")
    assert asyncio.run(_schema_diff(database_url)) == []

    command.downgrade(config, "base")
    assert not asyncio.run(_tables(database_url))
    command.upgrade(config, "head")
    assert "procrastinate_jobs" in asyncio.run(_tables(database_url))
