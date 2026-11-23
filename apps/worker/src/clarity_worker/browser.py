from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from playwright.async_api import Browser, BrowserContext, Page, Playwright, ProxySettings, Route

from clarity_core.domain.capture import RequestIssue
from clarity_core.domain.viewport import Viewport
from clarity_worker.policy import RequestPolicy, Verdict

MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
)

# Headless Chromium announces itself in the user agent and through navigator.webdriver,
# and some sites answer that with 403 or a challenge page instead of the real one.
STEALTH_ARGS = ["--disable-blink-features=AutomationControlled"]


async def launch_browser(
    playwright: Playwright, *, headless: bool, proxy: ProxySettings | None
) -> Browser:
    return await playwright.chromium.launch(
        headless=headless,
        proxy=proxy,
        args=STEALTH_ARGS,
        ignore_default_args=["--enable-automation"],
    )


@dataclass
class GuardedContext:
    context: BrowserContext
    viewport: Viewport
    policy: RequestPolicy
    blocked: list[RequestIssue] = field(default_factory=list)

    async def new_page(self) -> Page:
        return await self.context.new_page()

    async def _route(self, route: Route) -> None:
        request = route.request
        verdict = await self.policy.evaluate(request.method, request.url)
        if verdict is Verdict.ALLOW:
            await route.continue_()
            return
        self.blocked.append(
            RequestIssue(
                url=request.url,
                method=request.method,
                resource_type=request.resource_type,
                error=verdict.value,
            )
        )
        await route.abort("blockedbyclient")


@asynccontextmanager
async def open_context(
    browser: Browser, viewport: Viewport, policy: RequestPolicy
) -> AsyncIterator[GuardedContext]:
    context = await browser.new_context(
        viewport={"width": viewport.width, "height": viewport.height},
        device_scale_factor=viewport.scale,
        is_mobile=viewport.is_mobile,
        has_touch=viewport.is_mobile,
        user_agent=MOBILE_UA if viewport.is_mobile else None,
        service_workers="block",
        accept_downloads=False,
    )
    guarded = GuardedContext(context, viewport, policy)
    await context.route("**/*", guarded._route)
    try:
        yield guarded
    finally:
        await context.close()
