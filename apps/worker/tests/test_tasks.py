import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from clarity_core.domain.profile import AnalysisProfile, ScopeMode
from clarity_persistence.database import create_engine, session_factory
from clarity_persistence.jobs import ANALYSIS_QUEUE, RUN_ANALYSIS, create_job_app
from clarity_persistence.models import RunStatus
from clarity_persistence.repositories import RunRepository, SiteRepository
from clarity_worker.settings import WorkerSettings
from clarity_worker.tasks import build_jobs

ALEMBIC_INI = Path(__file__).resolve().parents[3] / "packages" / "persistence" / "alembic.ini"


async def migrate(url: str) -> None:
    engine = create_engine(url)
    async with engine.begin() as connection:
        await connection.execute(text("drop schema public cascade"))
        await connection.execute(text("create schema public"))
    await engine.dispose()
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("sqlalchemy.url", url)
    await asyncio.to_thread(command.upgrade, config, "head")


async def test_deferred_run_is_processed_by_the_worker(
    database_url: str, bugfarm: str, tmp_path: Path
) -> None:
    await migrate(database_url)
    engine = create_engine(database_url)
    sessions = session_factory(engine)
    async with sessions() as db:
        site = await SiteRepository(db).create(
            "Bugfarm", AnalysisProfile(start_url=f"{bugfarm}/about.html", scope=ScopeMode.SINGLE)
        )
        run = await RunRepository(db).create(site)
        await db.commit()

    producer = create_job_app(database_url)
    async with producer.open_async():
        await producer.configure_task(RUN_ANALYSIS, queue=ANALYSIS_QUEUE).defer_async(
            run_id=str(run.id)
        )

    settings = WorkerSettings(
        database_url=database_url,
        artifact_dir=tmp_path,
        allowed_networks=["127.0.0.0/8"],
        headless=True,
        _env_file=None,
    )
    jobs = build_jobs(settings)
    async with jobs.open_async():
        await jobs.run_worker_async(queues=[ANALYSIS_QUEUE], wait=False)

    async with sessions() as db:
        stored = await RunRepository(db).get(run.id)
        assert stored is not None
        assert stored.status is RunStatus.COMPLETED
        assert len(await RunRepository(db).pages(run.id)) == 2
    await engine.dispose()
    assert await asyncio.to_thread(lambda: any(tmp_path.rglob("section-00.png")))
