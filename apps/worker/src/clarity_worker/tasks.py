import logging
import uuid
from functools import cache
from pathlib import Path
from typing import Any

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import ProxySettings, async_playwright
from procrastinate import App

from clarity_ai.agents import RecommendationAgent, SimulationAgent
from clarity_ai.factory import create_provider
from clarity_ai.provider import LLMProvider, ProviderError
from clarity_core.domain.findings import Finding
from clarity_core.domain.profile import AnalysisProfile
from clarity_persistence.database import create_engine, session_factory
from clarity_persistence.jobs import ANALYSIS_QUEUE, RUN_ANALYSIS, SIMULATE_FIX, create_job_app
from clarity_persistence.models import FindingRecord, Run, Site
from clarity_persistence.repositories import SimulationRepository
from clarity_persistence.secrets import SecretBox, SiteLogin
from clarity_saliency.predictor import AttentionPredictor
from clarity_worker.predict import PagePredictor
from clarity_worker.review import PageReviewer
from clarity_worker.runner import AnalysisRunner
from clarity_worker.settings import WorkerSettings
from clarity_worker.simulation import FixSimulator, SimulationError
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

    @jobs.task(name=SIMULATE_FIX, queue=ANALYSIS_QUEUE)
    async def simulate_fix(simulation_id: str) -> None:
        await simulate(settings, uuid.UUID(simulation_id))

    return jobs


async def simulate(settings: WorkerSettings, simulation_id: uuid.UUID) -> None:
    engine = create_engine(settings.database_url)
    sessions = session_factory(engine)
    try:
        async with sessions() as db:
            simulations = SimulationRepository(db)
            simulation = await simulations.get(simulation_id)
            if simulation is None:
                return
            record = await db.get(FindingRecord, simulation.finding_id)
            run = await db.get(Run, simulation.run_id)
            site = await db.get(Site, run.site_id) if run else None
            attention = attention_predictor(settings.model_dir.resolve())
            provider = _provider(settings)
            if record is None or run is None or attention is None or provider is None:
                await simulations.finish(
                    simulation, error="simulations need saliency models and a review model"
                )
                await db.commit()
                return
            finding = Finding.model_validate(record.data)
            language = AnalysisProfile.model_validate(run.profile).language.value
            login = (
                SiteLogin.open(
                    SecretBox(settings.credentials_key.get_secret_value()), site.credentials
                )
                if site and site.credentials and settings.credentials_key
                else None
            )

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(proxy=_proxy(settings))
            try:
                simulator = FixSimulator(
                    browser,
                    LocalArtifactStore(settings.artifact_dir),
                    settings.guard(),
                    attention,
                    SimulationAgent(provider),
                )
                try:
                    patch, result = await simulator.simulate(
                        finding, language, f"{run.id}/simulations/{simulation_id}", login
                    )
                    outcome: dict[str, Any] = {
                        "patch": patch.model_dump(mode="json"),
                        "result": result,
                    }
                except (SimulationError, ProviderError, PlaywrightError) as exc:
                    outcome = {"error": str(exc).splitlines()[0][:500]}
            finally:
                await browser.close()

        async with sessions() as db:
            simulations = SimulationRepository(db)
            stored = await simulations.get(simulation_id)
            if stored:
                await simulations.finish(stored, **outcome)
                await db.commit()
    finally:
        await engine.dispose()


def _provider(settings: WorkerSettings) -> LLMProvider | None:
    return create_provider(
        settings.ai_provider,
        model=settings.ai_model,
        base_url=settings.ai_base_url,
        api_key=settings.ai_api_key.get_secret_value() if settings.ai_api_key else None,
    )


def _proxy(settings: WorkerSettings) -> ProxySettings | None:
    return {"server": settings.egress_proxy} if settings.egress_proxy else None


async def execute(settings: WorkerSettings, run_id: uuid.UUID) -> None:
    engine = create_engine(settings.database_url)
    proxy = _proxy(settings)
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(proxy=proxy)
            try:
                store = LocalArtifactStore(settings.artifact_dir)
                attention = attention_predictor(settings.model_dir.resolve())
                provider = _provider(settings)
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
