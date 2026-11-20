import logging
import uuid
from functools import cache
from pathlib import Path

from playwright.async_api import ProxySettings, async_playwright
from procrastinate import App

from clarity_ai.agents import RecommendationAgent
from clarity_ai.factory import create_provider
from clarity_persistence.database import create_engine, session_factory
from clarity_persistence.jobs import ANALYSIS_QUEUE, RUN_ANALYSIS, create_job_app
from clarity_persistence.secrets import SecretBox
from clarity_saliency.predictor import AttentionPredictor
from clarity_worker.predict import PagePredictor
from clarity_worker.review import PageReviewer
from clarity_worker.runner import AnalysisRunner
from clarity_worker.settings import WorkerSettings
from clarity_worker.store import LocalArtifactStore

log = logging.getLogger(__name__)


@cache
def attention_predictor(model_dir: Path) -> AttentionPredictor | None:
    if not any(model_dir.glob("*.onnx")):
        log.warning("no saliency models in %s; attention prediction is disabled", model_dir)
        return None
    return AttentionPredictor(model_dir)


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
                store = LocalArtifactStore(settings.artifact_dir)
                attention = attention_predictor(settings.model_dir.resolve())
                provider = create_provider(
                    settings.ai_provider,
                    model=settings.ai_model,
                    base_url=settings.ai_base_url,
                    api_key=settings.ai_api_key.get_secret_value() if settings.ai_api_key else None,
                )
                runner = AnalysisRunner(
                    session_factory(engine),
                    browser,
                    store,
                    settings.guard(),
                    predictor=PagePredictor(store, attention) if attention else None,
                    reviewer=PageReviewer(provider, store) if provider else None,
                    recommender=RecommendationAgent(provider) if provider else None,
                    secrets=(
                        SecretBox(settings.credentials_key.get_secret_value())
                        if settings.credentials_key
                        else None
                    ),
                )
                await runner.run(run_id)
            finally:
                await browser.close()
    finally:
        await engine.dispose()
