import logging
import uuid
from collections.abc import Awaitable, Callable

from playwright.async_api import Browser
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from clarity_ai.provider import ProviderError
from clarity_core.domain.capture import PageCapture
from clarity_core.domain.prediction import PagePrediction
from clarity_core.domain.probe import PageProbe
from clarity_core.domain.profile import AnalysisProfile
from clarity_core.domain.viewport import Viewport
from clarity_core.net.guard import AddressGuard
from clarity_persistence.models import PageRecord, Run, RunStatus
from clarity_persistence.repositories import RunRepository
from clarity_worker.checks import run_checks
from clarity_worker.explorer import SiteExplorer
from clarity_worker.predict import PagePredictor
from clarity_worker.review import CapturedView, PageReviewer
from clarity_worker.store import ArtifactStore

log = logging.getLogger(__name__)

PageHook = Callable[[PageCapture], Awaitable[None]]
VIEWPORT_ORDER = list(Viewport)


class RunCancelledError(Exception):
    pass


class AnalysisRunner:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        browser: Browser,
        store: ArtifactStore,
        guard: AddressGuard,
        *,
        predictor: PagePredictor | None = None,
        reviewer: PageReviewer | None = None,
        scroll_pause_ms: int = 250,
    ) -> None:
        self.sessions = sessions
        self.store = store
        self.explorer = SiteExplorer(browser, store, guard, scroll_pause_ms=scroll_pause_ms)
        self.predictor = predictor
        self.reviewer = reviewer
        self.after_page: PageHook | None = None

    async def run(self, run_id: uuid.UUID) -> None:
        async with self.sessions() as db:
            runs = RunRepository(db)
            run = await runs.get(run_id)
            if run is None or run.status.finished:
                return
            await runs.start(run)
            await runs.report(run, stage="explore", pages=0)
            await db.commit()
            profile = AnalysisProfile.model_validate(run.profile)

        try:
            exploration = await self.explorer.explore(
                profile, run_id=str(run_id), on_page=lambda capture: self._store(run_id, capture)
            )
        except RunCancelledError:
            log.info("run %s cancelled", run_id)
            return
        except Exception as exc:
            log.exception("run %s crashed", run_id)
            await self._finish(run_id, error=f"{type(exc).__name__}: {exc}")
            return

        failures = [f"{f.viewport} {f.url}: {f.reason}" for f in exploration.failures]
        if not exploration.pages:
            await self._finish(run_id, error="; ".join(failures) or "no pages captured")
            return

        for stage, step in (("prediction", self._predict), ("audit", self._audit)):
            try:
                await step(run_id)
            except RunCancelledError:
                log.info("run %s cancelled", run_id)
                return
            except Exception as exc:
                log.exception("run %s failed during %s", run_id, stage)
                await self._finish(run_id, error=f"{stage} failed: {type(exc).__name__}: {exc}")
                return
        await self._finish(run_id, failures=failures)

    async def _predict(self, run_id: uuid.UUID) -> None:
        if self.predictor is None:
            return
        async with self.sessions() as db:
            runs = RunRepository(db)
            run = await runs.get(run_id)
            if run is None or run.status is not RunStatus.RUNNING:
                raise RunCancelledError
            await runs.report(run, stage="predict", predicted=0)
            await db.commit()
            page_ids = [page.id for page in await runs.pages(run_id)]

        for done, page_id in enumerate(page_ids, start=1):
            async with self.sessions() as db:
                runs = RunRepository(db)
                run = await runs.get(run_id)
                page = await db.get(PageRecord, page_id)
                if run is None or run.status is not RunStatus.RUNNING:
                    raise RunCancelledError
                if page is None:
                    continue
                prediction = await self.predictor.predict(PageCapture.model_validate(page.capture))
                await runs.save_predictions(page, prediction)
                await runs.report(run, predicted=done)
                await db.commit()

    async def _store(self, run_id: uuid.UUID, capture: PageCapture) -> None:
        async with self.sessions() as db:
            runs = RunRepository(db)
            run = await runs.get(run_id)
            if run is None or run.status is not RunStatus.RUNNING:
                raise RunCancelledError
            await runs.add_page(run, capture)
            await runs.report(run, pages=run.progress.get("pages", 0) + 1)
            await db.commit()
        if self.after_page:
            await self.after_page(capture)

    async def _audit(self, run_id: uuid.UUID) -> None:
        async with self.sessions() as db:
            runs = RunRepository(db)
            run = await self._running(runs, run_id)
            language = str(run.profile.get("language", "en"))
            await runs.report(run, stage="audit", audited=0, findings=0)
            await db.commit()
            groups: dict[str, list[PageRecord]] = {}
            for page in await runs.pages(run_id):
                groups.setdefault(page.url, []).append(page)

        total = 0
        review_errors: list[str] = []
        reported: set[tuple[str, str, str]] = set()
        for done, records in enumerate(groups.values(), start=1):
            records.sort(key=lambda record: VIEWPORT_ORDER.index(Viewport(record.viewport)))
            views = [view for view in [await self._view(record) for record in records] if view]
            if not views:
                continue
            findings = run_checks(
                [(view.capture, view.probe) for view in views], language, reported
            )
            review = None
            if self.reviewer:
                try:
                    review = await self.reviewer.review(views, language)
                    findings.extend(review.findings)
                except ProviderError as exc:
                    log.warning("design review failed for %s: %s", records[0].url, exc)
                    review_errors.append(f"{records[0].url}: {exc}")

            page_ids = {Viewport(record.viewport): record.id for record in records}
            async with self.sessions() as db:
                runs = RunRepository(db)
                run = await self._running(runs, run_id)
                for viewport, page_id in page_ids.items():
                    batch = [finding for finding in findings if finding.viewport is viewport]
                    if batch:
                        await runs.add_findings(run, batch, page_id=page_id)
                if review:
                    lead = await db.get(PageRecord, records[0].id)
                    if lead:
                        await runs.save_review(
                            lead,
                            {
                                "understanding": review.understanding.model_dump(mode="json"),
                                **review.review.model_dump(mode="json", exclude={"notes"}),
                                "model": review.model,
                            },
                        )
                total += len(findings)
                await runs.report(run, audited=done, findings=total, review_errors=review_errors)
                await db.commit()

    async def _view(self, record: PageRecord) -> CapturedView | None:
        capture = PageCapture.model_validate(record.capture)
        if capture.probe is None:
            return None
        probe = PageProbe.model_validate_json(await self.store.get(capture.probe))
        prediction = (
            PagePrediction.model_validate(record.predictions) if record.predictions else None
        )
        return CapturedView(capture, probe, prediction)

    async def _running(self, runs: RunRepository, run_id: uuid.UUID) -> Run:
        run = await runs.get(run_id)
        if run is None or run.status is not RunStatus.RUNNING:
            raise RunCancelledError
        return run

    async def _finish(
        self, run_id: uuid.UUID, *, error: str | None = None, failures: list[str] | None = None
    ) -> None:
        async with self.sessions() as db:
            runs = RunRepository(db)
            run = await runs.get(run_id)
            if run is None or run.status.finished:
                return
            if error is not None:
                await runs.fail(run, error[:2000])
            else:
                await runs.report(run, stage="done", failures=failures or [])
                await runs.complete(run)
            await db.commit()
