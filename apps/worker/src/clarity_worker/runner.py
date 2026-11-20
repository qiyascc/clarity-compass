import logging
import uuid
from collections.abc import Awaitable, Callable

from playwright.async_api import Browser
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from clarity_core.domain.capture import PageCapture
from clarity_core.domain.profile import AnalysisProfile
from clarity_core.net.guard import AddressGuard
from clarity_persistence.models import RunStatus
from clarity_persistence.repositories import RunRepository
from clarity_worker.explorer import SiteExplorer
from clarity_worker.store import ArtifactStore

log = logging.getLogger(__name__)

PageHook = Callable[[PageCapture], Awaitable[None]]


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
        scroll_pause_ms: int = 250,
    ) -> None:
        self.sessions = sessions
        self.explorer = SiteExplorer(browser, store, guard, scroll_pause_ms=scroll_pause_ms)
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
        else:
            await self._finish(run_id, failures=failures)

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
