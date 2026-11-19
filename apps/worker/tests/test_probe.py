from playwright.async_api import Browser

from clarity_core.domain.viewport import Viewport
from clarity_core.net.guard import AddressGuard
from clarity_worker.browser import open_context
from clarity_worker.policy import RequestPolicy
from clarity_worker.probe import run_probe


async def test_probe_measures_the_rendered_page(
    browser: Browser, loopback_guard: AddressGuard, bugfarm: str
) -> None:
    async with open_context(browser, Viewport.DESKTOP, RequestPolicy(loopback_guard)) as context:
        page = await context.new_page()
        await page.goto(f"{bugfarm}/")
        probe = await run_probe(page)

    assert probe.title == "BugFarm Estates"
    assert probe.viewport.width == Viewport.DESKTOP.width
    assert [heading.text for heading in probe.headings][:2] == [
        "Find your next home",
        "Featured listings",
    ]

    subtitle = next(e for e in probe.elements if e.text.startswith("Thousands of verified"))
    assert subtitle.contrast is not None
    assert subtitle.contrast < 2

    header = next(e for e in probe.elements if e.text == "BugFarm Estates")
    assert header.position == "static"
    assert probe.landmarks["header"][0].height == 64

    tiny = next(e for e in probe.elements if e.name == "Learn more")
    assert tiny.interactive
    assert tiny.box.height < 24

    broken = next(i for i in probe.images if i.src.endswith("missing.jpg"))
    assert not broken.loaded


async def test_probe_survives_strict_csp(
    browser: Browser, loopback_guard: AddressGuard, bugfarm: str
) -> None:
    async with open_context(browser, Viewport.MOBILE, RequestPolicy(loopback_guard)) as context:
        page = await context.new_page()
        await page.goto(f"{bugfarm}/about.html")
        await page.evaluate(
            """() => {
                const meta = document.createElement('meta');
                meta.httpEquiv = 'Content-Security-Policy';
                meta.content = "script-src 'none'";
                document.head.append(meta);
            }"""
        )
        probe = await run_probe(page)
    assert probe.viewport.width == Viewport.MOBILE.width
    assert probe.interactive
