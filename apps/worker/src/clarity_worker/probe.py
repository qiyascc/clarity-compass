import os
from functools import cache
from pathlib import Path

from playwright.async_api import Page

from clarity_core.domain.probe import PageProbe

DEFAULT_BUNDLE = Path(__file__).resolve().parents[4] / "packages" / "probe" / "dist" / "probe.js"


class ProbeUnavailableError(RuntimeError):
    pass


@cache
def probe_source() -> str:
    path = Path(os.environ.get("CLARITY_PROBE_BUNDLE", DEFAULT_BUNDLE))
    if not path.is_file():
        raise ProbeUnavailableError(f"probe bundle not found at {path}; build packages/probe")
    return path.read_text()


async def run_probe(page: Page) -> PageProbe:
    installed = await page.evaluate("() => Boolean(window.__clarityProbe)")
    if not installed:
        await page.evaluate(probe_source())
    raw = await page.evaluate("() => window.__clarityProbe.collect()")
    return PageProbe.model_validate(raw)
