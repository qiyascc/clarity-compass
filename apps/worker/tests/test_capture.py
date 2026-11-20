from pathlib import Path

import pytest
from playwright.async_api import Browser

from clarity_core.domain.capture import PageCapture
from clarity_core.domain.probe import PageProbe
from clarity_core.domain.viewport import Viewport
from clarity_core.net.guard import AddressGuard
from clarity_worker.browser import open_context
from clarity_worker.capture import CaptureError, PageCapturer
from clarity_worker.policy import RequestPolicy
from clarity_worker.store import LocalArtifactStore


@pytest.fixture
def store(tmp_path: Path) -> LocalArtifactStore:
    return LocalArtifactStore(tmp_path)


async def capture(
    browser: Browser,
    guard: AddressGuard,
    store: LocalArtifactStore,
    url: str,
    viewport: Viewport = Viewport.DESKTOP,
) -> PageCapture:
    policy = RequestPolicy(guard)
    async with open_context(browser, viewport, policy) as context:
        return await PageCapturer(store, prefix="run").capture(context, url)


async def test_scroll_capture_produces_viewport_sections(
    browser: Browser, loopback_guard: AddressGuard, store: LocalArtifactStore, bugfarm: str
) -> None:
    result = await capture(browser, loopback_guard, store, f"{bugfarm}/")

    assert result.status == 200
    assert result.title == "BugFarm Estates"
    assert len(result.sections) >= 4
    assert [s.index for s in result.sections] == list(range(len(result.sections)))
    assert result.sections[-1].scroll_y + result.sections[-1].height == result.page_height
    for section in result.sections:
        assert (await store.get(section.screenshot)).startswith(b"\x89PNG")
    assert result.full_page is not None
    assert f"{bugfarm}/about.html" in result.links
    assert result.probe is not None
    probe = PageProbe.model_validate_json(await store.get(result.probe))
    assert probe.document_height == result.page_height
    assert result.snapshot is not None
    assert b"Find your next home" in await store.get(result.snapshot)


async def test_lazy_content_is_loaded_by_scrolling(
    browser: Browser, loopback_guard: AddressGuard, store: LocalArtifactStore, bugfarm: str
) -> None:
    result = await capture(browser, loopback_guard, store, f"{bugfarm}/")
    assert result.grew_while_scrolling


async def test_console_and_resource_failures_are_recorded(
    browser: Browser, loopback_guard: AddressGuard, store: LocalArtifactStore, bugfarm: str
) -> None:
    result = await capture(browser, loopback_guard, store, f"{bugfarm}/")

    assert any("analytics" in entry.text for entry in result.console if entry.level == "error")
    broken = [issue for issue in result.request_issues if issue.url.endswith("/img/missing.jpg")]
    assert broken
    assert broken[0].status == 404


async def test_mobile_viewport_uses_device_width(
    browser: Browser, loopback_guard: AddressGuard, store: LocalArtifactStore, bugfarm: str
) -> None:
    result = await capture(browser, loopback_guard, store, f"{bugfarm}/", Viewport.MOBILE)
    assert result.viewport is Viewport.MOBILE
    assert all(section.height <= Viewport.MOBILE.height for section in result.sections)


async def test_missing_page_reports_status(
    browser: Browser, loopback_guard: AddressGuard, store: LocalArtifactStore, bugfarm: str
) -> None:
    result = await capture(browser, loopback_guard, store, f"{bugfarm}/listings/404.html")
    assert result.status == 404


async def test_private_target_is_refused_without_allowlist(
    browser: Browser, store: LocalArtifactStore, bugfarm: str
) -> None:
    with pytest.raises(CaptureError, match="blocked"):
        await capture(browser, AddressGuard(), store, f"{bugfarm}/")


async def test_mutating_requests_from_page_are_blocked(
    browser: Browser, loopback_guard: AddressGuard, bugfarm: str
) -> None:
    async with open_context(browser, Viewport.DESKTOP, RequestPolicy(loopback_guard)) as context:
        page = await context.new_page()
        await page.goto(f"{bugfarm}/")
        outcome = await page.evaluate(
            "() => fetch('/api/lead', {method: 'POST'}).then(() => 'sent', () => 'blocked')"
        )
    assert outcome == "blocked"
    assert context.blocked[0].method == "POST"


async def test_pages_that_cannot_scroll_do_not_loop(
    browser: Browser, loopback_guard: AddressGuard, store: LocalArtifactStore, bugfarm: str
) -> None:
    result = await capture(
        browser, loopback_guard, store, f"{bugfarm}/listings/404.html", Viewport.MOBILE
    )
    assert result.status == 404
    assert 1 <= len(result.sections) <= 3
