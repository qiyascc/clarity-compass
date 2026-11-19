import os
from functools import cache
from pathlib import Path

from playwright.async_api import Page

from clarity_core.domain.probe import PageProbe

BUNDLE_DIR = Path(__file__).resolve().parents[4] / "packages" / "probe" / "dist"


class ProbeUnavailableError(RuntimeError):
    pass


@cache
def bundle_source(name: str) -> str:
    path = Path(os.environ.get("CLARITY_BUNDLE_DIR", BUNDLE_DIR)) / f"{name}.js"
    if not path.is_file():
        raise ProbeUnavailableError(f"bundle not found at {path}; build packages/probe")
    return path.read_text()


async def _ensure(page: Page, name: str, handle: str) -> None:
    if not await page.evaluate(f"() => Boolean(window.{handle})"):
        await page.evaluate(bundle_source(name))


async def run_probe(page: Page) -> PageProbe:
    await _ensure(page, "probe", "__clarityProbe")
    raw = await page.evaluate("() => window.__clarityProbe.collect()")
    return PageProbe.model_validate(raw)


async def take_snapshot(page: Page) -> bytes:
    await _ensure(page, "snapshot", "__claritySnapshot")
    serialised: str = await page.evaluate("() => JSON.stringify(window.__claritySnapshot.take())")
    return serialised.encode()
