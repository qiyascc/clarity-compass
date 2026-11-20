import json
from pathlib import Path

import pytest
from playwright.async_api import Browser

from clarity_core.domain.findings import EvidenceKind, Finding, Status
from clarity_core.domain.viewport import Viewport
from clarity_core.net.guard import AddressGuard
from clarity_worker.browser import open_context
from clarity_worker.functional.auditor import FunctionalAuditor
from clarity_worker.policy import RequestPolicy
from clarity_worker.store import LocalArtifactStore


async def audit(
    browser: Browser,
    guard: AddressGuard,
    store: LocalArtifactStore,
    url: str,
    viewport: Viewport = Viewport.DESKTOP,
) -> list[Finding]:
    auditor = FunctionalAuditor(store, guard, language="en", max_actions=20, prefix="run/home")
    async with open_context(browser, viewport, RequestPolicy(guard)) as context:
        return await auditor.audit(context, url)


@pytest.fixture
def store(tmp_path: Path) -> LocalArtifactStore:
    return LocalArtifactStore(tmp_path)


async def test_planted_interaction_defects_are_found(
    browser: Browser, loopback_guard: AddressGuard, store: LocalArtifactStore, bugfarm: str
) -> None:
    findings = await audit(browser, loopback_guard, store, f"{bugfarm}/")
    by_rule = {f.source.removeprefix("functional:"): f for f in findings}
    no_effect = {
        f.anchor.selector for f in findings if f.source == "functional:no-effect" and f.anchor
    }

    assert "#search-btn" in no_effect
    assert by_rule["click-error"].anchor
    assert by_rule["click-error"].anchor.selector == "#to-top"
    assert "scrollToTop" in by_rule["click-error"].description
    assert "#nowhere" in by_rule["anchor-missing"].description
    assert "404" in by_rule["broken-link"].description
    assert by_rule["language-partial"].anchor
    assert by_rule["language-partial"].anchor.selector == "#lang"
    assert by_rule["menu-no-close"].anchor
    assert by_rule["menu-no-close"].anchor.selector == "#filters"
    assert by_rule["dialog-no-close"].anchor
    assert by_rule["dialog-no-close"].anchor.selector == "#newsletter"

    for finding in findings:
        assert finding.status is Status.VERIFIED
        trace = next(e for e in finding.evidence if e.kind is EvidenceKind.ACTION_TRACE)
        recorded = json.loads(await store.get(trace.ref))
        assert recorded["steps"]


@pytest.mark.parametrize("path", ["/about.html", "/contact.html"])
async def test_working_controls_are_not_reported(
    browser: Browser,
    loopback_guard: AddressGuard,
    store: LocalArtifactStore,
    bugfarm: str,
    path: str,
) -> None:
    findings = await audit(browser, loopback_guard, store, f"{bugfarm}{path}")
    assert findings == []
