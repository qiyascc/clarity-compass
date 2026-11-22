from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import pytest
from playwright.async_api import Browser

from clarity_core.domain.profile import AnalysisProfile, CrawlLimits, ScopeMode
from clarity_core.domain.viewport import Viewport
from clarity_core.net.guard import AddressGuard
from clarity_worker import explorer as explorer_module
from clarity_worker.browser import GuardedContext, open_context
from clarity_worker.explorer import SiteExplorer
from clarity_worker.store import LocalArtifactStore


@pytest.fixture
def explorer(browser: Browser, loopback_guard: AddressGuard, tmp_path: Path) -> SiteExplorer:
    return SiteExplorer(browser, LocalArtifactStore(tmp_path), loopback_guard, scroll_pause_ms=50)


def paths(urls: list[str], origin: str) -> set[str]:
    return {url.removeprefix(origin) for url in urls}


async def test_site_scope_follows_links_and_sitemap(explorer: SiteExplorer, bugfarm: str) -> None:
    profile = AnalysisProfile(
        start_url=bugfarm, viewports=[Viewport.DESKTOP], limits=CrawlLimits(max_pages=20)
    )
    result = await explorer.explore(profile, run_id="r1")

    visited = paths([page.requested_url for page in result.pages], bugfarm)
    assert visited >= {"/", "/about.html", "/contact.html", "/listings/", "/listings/1.html"}
    assert "/listings/404.html" in visited
    statuses = {page.requested_url.removeprefix(bugfarm): page.status for page in result.pages}
    assert statuses["/listings/404.html"] == 404
    assert not result.failures


async def test_page_limit_is_respected(explorer: SiteExplorer, bugfarm: str) -> None:
    profile = AnalysisProfile(
        start_url=bugfarm, viewports=[Viewport.DESKTOP], limits=CrawlLimits(max_pages=2)
    )
    result = await explorer.explore(profile, run_id="r2")
    assert len(result.pages) == 2


async def test_pages_scope_visits_only_selected_pages(explorer: SiteExplorer, bugfarm: str) -> None:
    profile = AnalysisProfile(
        start_url=bugfarm,
        scope=ScopeMode.PAGES,
        pages=[f"{bugfarm}/about.html", f"{bugfarm}/listings/1.html"],
        viewports=[Viewport.DESKTOP],
    )
    result = await explorer.explore(profile, run_id="r3")
    assert paths([p.requested_url for p in result.pages], bugfarm) == {
        "/about.html",
        "/listings/1.html",
    }


async def test_every_page_is_captured_in_every_viewport(
    explorer: SiteExplorer, bugfarm: str
) -> None:
    profile = AnalysisProfile(
        start_url=f"{bugfarm}/about.html",
        scope=ScopeMode.SINGLE,
        viewports=[Viewport.DESKTOP, Viewport.MOBILE],
    )
    result = await explorer.explore(profile, run_id="r4")
    assert sorted(page.viewport for page in result.pages) == [Viewport.DESKTOP, Viewport.MOBILE]


async def test_progress_callback_sees_each_capture(explorer: SiteExplorer, bugfarm: str) -> None:
    seen: list[str] = []

    async def on_page(capture: object) -> None:
        seen.append(getattr(capture, "requested_url", ""))

    profile = AnalysisProfile(
        start_url=f"{bugfarm}/about.html", scope=ScopeMode.SINGLE, viewports=[Viewport.DESKTOP]
    )
    await explorer.explore(profile, run_id="r5", on_page=on_page)
    assert seen == [f"{bugfarm}/about.html"]


async def test_signs_in_once_and_shares_the_session(
    explorer: SiteExplorer, bugfarm: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened: list[GuardedContext] = []

    @asynccontextmanager
    async def recording(*args: Any) -> AsyncIterator[GuardedContext]:
        async with open_context(*args) as context:
            opened.append(context)
            yield context

    monkeypatch.setattr(explorer_module, "open_context", recording)
    prepared: list[GuardedContext] = []

    async def prepare(context: GuardedContext) -> str:
        prepared.append(context)
        await context.context.add_cookies([{"name": "session", "value": "s1", "url": bugfarm}])
        return f"{bugfarm}/about.html"

    sessions: list[list[str]] = []

    async def on_page(capture: object) -> None:
        sessions.append([c["value"] for ctx in opened for c in await ctx.context.cookies()])

    profile = AnalysisProfile(
        start_url=f"{bugfarm}/about.html",
        scope=ScopeMode.SINGLE,
        viewports=[Viewport.DESKTOP, Viewport.MOBILE],
    )
    await explorer.explore(profile, run_id="r6", on_page=on_page, prepare=prepare)

    assert prepared == opened[:1]
    assert sessions
    assert all(values.count("s1") == 2 for values in sessions)
