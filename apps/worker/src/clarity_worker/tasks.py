import uuid

from playwright.async_api import ProxySettings, async_playwright
from procrastinate import App

from clarity_persistence.database import create_engine, session_factory
from clarity_persistence.jobs import ANALYSIS_QUEUE, RUN_ANALYSIS, create_job_app
from clarity_worker.runner import AnalysisRunner
from clarity_worker.settings import WorkerSettings
from clarity_worker.store import LocalArtifactStore


def build_jobs(settings: WorkerSettings) -> App:
    jobs = create_job_app(settings.database_url)

    @jobs.task(name=RUN_ANALYSIS, queue=ANALYSIS_QUEUE)
    async def run_analysis(run_id: str) -> None:
        await execute(settings, uuid.UUID(run_id))

    return jobs


async def execute(settings: WorkerSettings, run_id: uuid.UUID) -> None:
    engine = create_engine(settings.database_url)
    proxy: ProxySettings | None = (
        {"server": settings.egress_proxy} if settings.egress_proxy else None
    )
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(proxy=proxy)
            try:
                runner = AnalysisRunner(
                    session_factory(engine),
                    browser,
                    LocalArtifactStore(settings.artifact_dir),
                    settings.guard(),
                )
                await runner.run(run_id)
            finally:
                await browser.close()
    finally:
        await engine.dispose()
