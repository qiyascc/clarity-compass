from typing import Any, cast

from playwright.async_api import Playwright

from clarity_worker.browser import launch_browser


class FakeChromium:
    def __init__(self) -> None:
        self.options: dict[str, Any] = {}

    async def launch(self, **options: Any) -> str:
        self.options = options
        return "browser"


class FakePlaywright:
    def __init__(self) -> None:
        self.chromium = FakeChromium()


async def test_launch_hides_automation_markers() -> None:
    playwright = FakePlaywright()

    await launch_browser(
        cast(Playwright, playwright), headless=False, proxy={"server": "http://egress:4750"}
    )

    options = playwright.chromium.options
    assert options["headless"] is False
    assert options["proxy"] == {"server": "http://egress:4750"}
    assert "--disable-blink-features=AutomationControlled" in options["args"]
    assert options["ignore_default_args"] == ["--enable-automation"]
