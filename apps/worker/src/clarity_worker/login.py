import contextlib
from dataclasses import dataclass

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Locator, Page

from clarity_core.net.guard import UnsafeTargetError
from clarity_core.net.urls import same_site
from clarity_persistence.secrets import SiteLogin
from clarity_worker.browser import GuardedContext

USERNAME_FIELDS = (
    "input[autocomplete=username], input[autocomplete=email], input[type=email], "
    "input[name*=user i], input[name*=login i], input[name*=email i], input[type=text]"
)
TIMEOUT_MS = 15_000


@dataclass(frozen=True)
class LoginResult:
    signed_in: bool
    reason: str
    landed_on: str | None = None


async def sign_in(context: GuardedContext, login: SiteLogin) -> LoginResult:
    """Signs in through the site's own form, allowing writes only for that submission."""
    try:
        await context.policy.guard.check_url(login.login_url)
    except UnsafeTargetError as exc:
        return LoginResult(False, f"login page refused: {exc}")

    page = await context.new_page()
    try:
        await page.goto(login.login_url, wait_until="load", timeout=30_000)
        password = await _field(page, login.password_selector or "input[type=password]")
        if password is None:
            return LoginResult(False, "no password field on the login page")
        username = await _username(page, login, password)
        if username is None:
            return LoginResult(False, "no username field on the login page")

        await username.fill(login.username)
        await password.fill(login.password)
        context.policy.allow_mutations_to(login.login_url)
        try:
            await _submit(page, login, password)
            with contextlib.suppress(PlaywrightError):
                await page.wait_for_load_state("networkidle", timeout=TIMEOUT_MS)
        finally:
            context.policy.allow_mutations_to(None)

        still_asking = await _field(page, login.password_selector or "input[type=password]")
        if still_asking is not None and await still_asking.is_visible():
            return LoginResult(False, "the login form is still shown after submitting", page.url)
        if not same_site(page.url, login.login_url):
            return LoginResult(False, f"login left the site for {page.url}", page.url)
        return LoginResult(True, "signed in", page.url)
    except PlaywrightError as exc:
        return LoginResult(False, f"login failed: {str(exc).splitlines()[0]}")
    finally:
        await page.close()


async def _field(page: Page, selector: str) -> Locator | None:
    locator = page.locator(selector).filter(visible=True).first
    return locator if await locator.count() else None


async def _username(page: Page, login: SiteLogin, password: Locator) -> Locator | None:
    if login.username_selector:
        return await _field(page, login.username_selector)
    form = password.locator("xpath=ancestor::form[1]")
    scope = form if await form.count() else page.locator("body")
    candidate = scope.locator(USERNAME_FIELDS).filter(visible=True).first
    return candidate if await candidate.count() else None


async def _submit(page: Page, login: SiteLogin, password: Locator) -> None:
    if login.submit_selector:
        await page.locator(login.submit_selector).first.click(timeout=TIMEOUT_MS)
        return
    form = password.locator("xpath=ancestor::form[1]")
    button = form.locator("button[type=submit], input[type=submit], button:not([type])").first
    if await form.count() and await button.count():
        await button.click(timeout=TIMEOUT_MS)
    else:
        await password.press("Enter")
