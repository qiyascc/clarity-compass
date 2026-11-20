from playwright.async_api import Browser

from clarity_core.domain.viewport import Viewport
from clarity_core.net.guard import AddressGuard
from clarity_persistence.secrets import SiteLogin
from clarity_worker.browser import open_context
from clarity_worker.login import sign_in
from clarity_worker.policy import RequestPolicy


async def test_signs_in_and_keeps_the_session(
    browser: Browser, loopback_guard: AddressGuard, bugfarm: str
) -> None:
    login = SiteLogin(f"{bugfarm}/login.html", "demo@bugfarm.test", "correct-horse")
    async with open_context(browser, Viewport.DESKTOP, RequestPolicy(loopback_guard)) as context:
        result = await sign_in(context, login)
        assert result.signed_in, result.reason
        assert result.landed_on == f"{bugfarm}/account.html"

        page = await context.new_page()
        await page.goto(f"{bugfarm}/account-saved.html")
        assert await page.title() == "Saved listings - BugFarm Estates"
        outcome = await page.evaluate(
            "() => fetch('/session', {method: 'POST'}).then(() => 'sent', () => 'blocked')"
        )
        assert outcome == "blocked"


async def test_wrong_password_is_reported(
    browser: Browser, loopback_guard: AddressGuard, bugfarm: str
) -> None:
    login = SiteLogin(f"{bugfarm}/login.html", "demo@bugfarm.test", "wrong")
    async with open_context(browser, Viewport.MOBILE, RequestPolicy(loopback_guard)) as context:
        result = await sign_in(context, login)
    assert not result.signed_in
    assert "still shown" in result.reason


async def test_explicit_selectors_are_used(
    browser: Browser, loopback_guard: AddressGuard, bugfarm: str
) -> None:
    login = SiteLogin(
        f"{bugfarm}/login.html",
        "demo@bugfarm.test",
        "correct-horse",
        username_selector="#email",
        password_selector="#password",
        submit_selector="form button",
    )
    async with open_context(browser, Viewport.DESKTOP, RequestPolicy(loopback_guard)) as context:
        assert (await sign_in(context, login)).signed_in
