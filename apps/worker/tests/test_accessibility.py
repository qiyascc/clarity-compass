import pytest
from playwright.async_api import Browser

from clarity_core.domain.findings import Status
from clarity_core.domain.viewport import Viewport
from clarity_core.net.guard import AddressGuard
from clarity_worker.accessibility import audit_accessibility
from clarity_worker.browser import open_context
from clarity_worker.policy import RequestPolicy


@pytest.mark.parametrize(("language", "fragment"), [("en", "discernible text"), ("ru", "кнопк")])
async def test_axe_violations_become_localized_verified_findings(
    browser: Browser, loopback_guard: AddressGuard, bugfarm: str, language: str, fragment: str
) -> None:
    async with open_context(browser, Viewport.DESKTOP, RequestPolicy(loopback_guard)) as context:
        findings = await audit_accessibility(context, f"{bugfarm}/", language)

    names = [f for f in findings if f.source == "axe:button-name"]
    assert names
    assert names[0].anchor is not None
    assert names[0].anchor.selector == ".save"
    assert fragment in (names[0].title + names[0].recommendation).lower()
    assert all(f.status is Status.VERIFIED for f in findings)
    assert not any(f.source == "axe:color-contrast" for f in findings)
