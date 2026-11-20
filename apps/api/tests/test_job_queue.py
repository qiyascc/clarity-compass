import asyncio
import uuid
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from clarity_api.queue import JobQueue
from clarity_api.settings import Settings
from clarity_persistence.database import create_engine
from clarity_persistence.jobs import ANALYSIS_QUEUE, RUN_ANALYSIS, create_job_app

ALEMBIC_INI = Path(__file__).resolve().parents[3] / "packages" / "persistence" / "alembic.ini"


async def test_enqueue_defers_a_procrastinate_job(settings: Settings) -> None:
    engine = create_engine(settings.database_url)
    async with engine.begin() as connection:
        await connection.execute(text("drop schema public cascade"))
        await connection.execute(text("create schema public"))
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    await asyncio.to_thread(command.upgrade, config, "head")

    queue = JobQueue(create_job_app(settings.database_url))
    run_id = uuid.uuid4()
    async with queue.lifespan():
        await queue.enqueue(run_id)

    async with engine.connect() as connection:
        row = (
            await connection.execute(
                text("select task_name, queue_name, args from procrastinate_jobs")
            )
        ).one()
    await engine.dispose()
    assert row.task_name == RUN_ANALYSIS
    assert row.queue_name == ANALYSIS_QUEUE
    assert row.args == {"run_id": str(run_id)}
