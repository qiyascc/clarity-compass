from pathlib import Path

import pytest
from playwright.async_api import Browser

from clarity_core.domain.capture import PageCapture
from clarity_core.domain.findings import Category, Status
from clarity_core.domain.probe import PageProbe
from clarity_core.domain.viewport import Viewport
from clarity_core.net.guard import AddressGuard
from clarity_worker.browser import open_context
from clarity_worker.capture import PageCapturer
from clarity_worker.checks import run_checks
from clarity_worker.checks.messages import CATALOG, placeholders
from clarity_worker.policy import RequestPolicy
from clarity_worker.store import LocalArtifactStore


async def captured(
    browser: Browser, guard: AddressGuard, store: LocalArtifactStore, url: str
) -> list[tuple[PageCapture, PageProbe]]:
    pages = []
    for viewport in (Viewport.DESKTOP, Viewport.MOBILE):
        async with open_context(browser, viewport, RequestPolicy(guard)) as context:
            capture = await PageCapturer(store, "run", scroll_pause_ms=50).capture(context, url)
        assert capture.probe is not None
        pages.append((capture, PageProbe.model_validate_json(await store.get(capture.probe))))
    return pages


@pytest.fixture
def store(tmp_path: Path) -> LocalArtifactStore:
    return LocalArtifactStore(tmp_path)


async def test_home_page_defects_are_found_and_verified(
    browser: Browser, loopback_guard: AddressGuard, store: LocalArtifactStore, bugfarm: str
) -> None:
    findings = run_checks(await captured(browser, loopback_guard, store, f"{bugfarm}/"), "en")
    by_rule: dict[str, list[str | None]] = {}
    for finding in findings:
        assert finding.status is Status.VERIFIED
        assert finding.evidence
        by_rule.setdefault(finding.source, []).append(
            finding.anchor.selector if finding.anchor else None
        )

    assert by_rule["check:low-contrast"]
    broken = [f for f in findings if f.source == "check:broken-image"]
    assert [e.ref for f in broken for e in f.evidence] == [f"GET {bugfarm}/img/missing.jpg"]
    assert by_rule["check:console-errors"] == [None]
    assert by_rule["check:small-tap-target"]
    assert "check:no-h1" not in by_rule
    contrast = next(f for f in findings if f.source == "check:low-contrast")
    assert contrast.category is Category.ACCESSIBILITY
    assert "Thousands of verified listings" in contrast.description


async def test_missing_alt_and_error_status(
    browser: Browser, loopback_guard: AddressGuard, store: LocalArtifactStore, bugfarm: str
) -> None:
    listing = run_checks(
        await captured(browser, loopback_guard, store, f"{bugfarm}/listings/1.html"), "tr"
    )
    alt = [f for f in listing if f.source == "check:missing-alt"]
    assert len(alt) == 1
    assert alt[0].title == "Görselin alternatif metni yok"

    missing = run_checks(
        await captured(browser, loopback_guard, store, f"{bugfarm}/listings/404.html"), "en"
    )
    status = [f for f in missing if f.source == "check:error-status"]
    assert [f.title for f in status] == ["Page responds with HTTP 404"]


def test_every_language_uses_the_same_placeholders() -> None:
    for key, translations in CATALOG.items():
        assert set(translations) == {"en", "tr", "az", "ru"}, key
        expected = placeholders(key, "en")
        for language in translations:
            assert placeholders(key, language) == expected, (key, language)
