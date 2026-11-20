import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
from playwright.async_api import Browser
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from clarity_ai.provider import Generated, Prompt, ProviderError
from clarity_ai.schemas import DesignReview, PageKind, PageUnderstanding, ReviewNote, Scores
from clarity_core.domain.capture import PageCapture
from clarity_core.domain.findings import Finding
from clarity_core.domain.prediction import PagePrediction
from clarity_core.domain.profile import AnalysisProfile, CrawlLimits, ScopeMode
from clarity_core.domain.viewport import Viewport
from clarity_core.net.guard import AddressGuard
from clarity_persistence.database import create_engine, session_factory
from clarity_persistence.models import RunStatus
from clarity_persistence.repositories import RunRepository, SiteRepository
from clarity_saliency.predictor import AttentionPredictor
from clarity_worker.predict import PagePredictor
from clarity_worker.review import PageReviewer
from clarity_worker.runner import AnalysisRunner
from clarity_worker.store import LocalArtifactStore

Sessions = async_sessionmaker[AsyncSession]
MODEL_DIR = Path(__file__).resolve().parents[3] / "models"


def model_predictor() -> AttentionPredictor:
    if not any(MODEL_DIR.glob("*.onnx")):
        pytest.skip("saliency models are not available")
    return AttentionPredictor(MODEL_DIR)


@pytest.fixture
async def sessions(database_url: str) -> AsyncIterator[Sessions]:
    engine = create_engine(database_url)
    yield session_factory(engine)
    await engine.dispose()


@pytest.fixture
def runner(
    sessions: Sessions, browser: Browser, loopback_guard: AddressGuard, tmp_path: Path
) -> AnalysisRunner:
    return AnalysisRunner(
        sessions, browser, LocalArtifactStore(tmp_path), loopback_guard, scroll_pause_ms=50
    )


async def queue_run(sessions: Sessions, profile: AnalysisProfile) -> uuid.UUID:
    async with sessions() as db:
        site = await SiteRepository(db).create("Bugfarm", profile)
        run = await RunRepository(db).create(site)
        await db.commit()
        return run.id


async def test_run_explores_and_stores_pages(
    runner: AnalysisRunner, sessions: Sessions, bugfarm: str
) -> None:
    run_id = await queue_run(
        sessions,
        AnalysisProfile(
            start_url=bugfarm, viewports=[Viewport.DESKTOP], limits=CrawlLimits(max_pages=3)
        ),
    )
    await runner.run(run_id)

    async with sessions() as db:
        runs = RunRepository(db)
        run = await runs.get(run_id)
        assert run is not None
        assert run.status is RunStatus.COMPLETED
        assert run.progress["pages"] == 3
        pages = await runs.pages(run_id)
    assert len(pages) == 3
    first = PageCapture.model_validate(pages[0].capture)
    assert first.sections
    assert first.probe is not None


async def test_predictions_are_stored_for_every_page(
    sessions: Sessions, browser: Browser, loopback_guard: AddressGuard, tmp_path: Path, bugfarm: str
) -> None:
    attention = model_predictor()
    store = LocalArtifactStore(tmp_path)
    runner = AnalysisRunner(
        sessions,
        browser,
        store,
        loopback_guard,
        predictor=PagePredictor(store, attention),
        scroll_pause_ms=50,
    )
    run_id = await queue_run(
        sessions, AnalysisProfile(start_url=f"{bugfarm}/about.html", scope=ScopeMode.SINGLE)
    )
    await runner.run(run_id)

    async with sessions() as db:
        runs = RunRepository(db)
        run = await runs.get(run_id)
        pages = await runs.pages(run_id)
    assert run is not None
    assert run.status is RunStatus.COMPLETED
    assert run.progress["predicted"] == len(pages) == 2
    for page in pages:
        assert page.predictions is not None
        assert PagePrediction.model_validate(page.predictions).sections


async def test_finished_runs_are_skipped(
    runner: AnalysisRunner, sessions: Sessions, bugfarm: str
) -> None:
    run_id = await queue_run(sessions, AnalysisProfile(start_url=bugfarm))
    async with sessions() as db:
        runs = RunRepository(db)
        run = await runs.get(run_id)
        assert run is not None
        await runs.cancel(run)
        await db.commit()

    await runner.run(run_id)

    async with sessions() as db:
        assert await RunRepository(db).pages(run_id) == []


async def test_cancellation_stops_exploration(
    runner: AnalysisRunner, sessions: Sessions, bugfarm: str
) -> None:
    run_id = await queue_run(
        sessions,
        AnalysisProfile(
            start_url=bugfarm, viewports=[Viewport.DESKTOP], limits=CrawlLimits(max_pages=10)
        ),
    )

    async def cancel_after_first(capture: PageCapture) -> None:
        async with sessions() as db:
            runs = RunRepository(db)
            run = await runs.get(run_id)
            assert run is not None
            if run.status is RunStatus.RUNNING:
                await runs.cancel(run)
                await db.commit()

    runner.after_page = cancel_after_first
    await runner.run(run_id)

    async with sessions() as db:
        runs = RunRepository(db)
        run = await runs.get(run_id)
        assert run is not None
        assert run.status is RunStatus.CANCELLED
        assert len(await runs.pages(run_id)) <= 2


async def test_failures_mark_the_run_failed(
    sessions: Sessions, browser: Browser, tmp_path: Path, bugfarm: str
) -> None:
    run_id = await queue_run(sessions, AnalysisProfile(start_url=bugfarm, scope=ScopeMode.SINGLE))
    strict = AnalysisRunner(sessions, browser, LocalArtifactStore(tmp_path), AddressGuard())
    await strict.run(run_id)

    async with sessions() as db:
        run = await RunRepository(db).get(run_id)
    assert run is not None
    assert run.status is RunStatus.FAILED
    assert run.error is not None
    assert "blocked" in run.error


class FailingProvider:
    name = "failing"
    model = "failing-1"

    async def structured(self, prompt: object, schema: object) -> object:
        raise ProviderError("Claude returned 529: overloaded")


class ScriptedProvider:
    name = "scripted"
    model = "scripted-1"

    async def structured(self, prompt: Prompt, schema: type[Any]) -> Generated[Any]:
        if schema is PageUnderstanding:
            return Generated(
                PageUnderstanding(
                    kind=PageKind.ABOUT,
                    purpose="Introduce the agency.",
                    audience="Buyers",
                    primary_action=None,
                    primary_element=None,
                    site_language="en",
                ),
                self.model,
            )
        return Generated(
            DesignReview(
                overall="Thin page.",
                strengths=[],
                scores=Scores(visual=50, ux=50, content=30, conversion=20, accessibility=60),
                notes=[
                    ReviewNote(
                        element=None,
                        viewport="all",
                        category="content",
                        severity="medium",
                        confidence=0.7,
                        title="The about page says almost nothing",
                        description="d",
                        recommendation="r",
                        alternative=None,
                        evidence="desktop section 1",
                    )
                ],
            ),
            self.model,
        )


async def test_audit_stores_checks_and_design_review(
    sessions: Sessions, browser: Browser, loopback_guard: AddressGuard, tmp_path: Path, bugfarm: str
) -> None:
    store = LocalArtifactStore(tmp_path)
    runner = AnalysisRunner(
        sessions,
        browser,
        store,
        loopback_guard,
        reviewer=PageReviewer(ScriptedProvider(), store),
        scroll_pause_ms=50,
    )
    run_id = await queue_run(
        sessions, AnalysisProfile(start_url=f"{bugfarm}/", scope=ScopeMode.SINGLE)
    )
    await runner.run(run_id)

    async with sessions() as db:
        runs = RunRepository(db)
        run = await runs.get(run_id)
        findings = [Finding.model_validate(record.data) for record in await runs.findings(run_id)]
        pages = await runs.pages(run_id)
    assert run is not None
    assert run.status is RunStatus.COMPLETED
    assert run.progress["audited"] == 1
    sources = {finding.source for finding in findings}
    assert {"check:console-errors", "check:broken-image", "agent:ux-designer"} <= sources
    lead = next(page for page in pages if page.viewport == "desktop")
    assert lead.review is not None
    assert lead.review["understanding"]["kind"] == "about"
    assert lead.review["scores"]["content"] == 30


async def test_review_failures_do_not_fail_the_run(
    sessions: Sessions, browser: Browser, loopback_guard: AddressGuard, tmp_path: Path, bugfarm: str
) -> None:
    store = LocalArtifactStore(tmp_path)
    runner = AnalysisRunner(
        sessions,
        browser,
        store,
        loopback_guard,
        reviewer=PageReviewer(FailingProvider(), store),  # type: ignore[arg-type]
        scroll_pause_ms=50,
    )
    run_id = await queue_run(
        sessions, AnalysisProfile(start_url=f"{bugfarm}/about.html", scope=ScopeMode.SINGLE)
    )
    await runner.run(run_id)

    async with sessions() as db:
        run = await RunRepository(db).get(run_id)
    assert run is not None
    assert run.status is RunStatus.COMPLETED
    assert "overloaded" in run.progress["review_errors"][0]
