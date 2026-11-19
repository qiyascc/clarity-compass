import ipaddress
import subprocess
import threading
from collections.abc import AsyncIterator, Iterator
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from playwright.async_api import Browser, async_playwright

from clarity_core.net.guard import AddressGuard

FIXTURE_ROOT = Path(__file__).resolve().parents[3] / "fixtures" / "bugfarmcc"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


@pytest.fixture(scope="session")
def bugfarm() -> Iterator[str]:
    handler = partial(QuietHandler, directory=str(FIXTURE_ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


@pytest.fixture
def loopback_guard() -> AddressGuard:
    return AddressGuard(allow=[ipaddress.ip_network("127.0.0.0/8")])


@pytest.fixture
async def browser() -> AsyncIterator[Browser]:
    async with async_playwright() as playwright:
        instance = await playwright.chromium.launch()
        yield instance
        await instance.close()


@pytest.fixture(scope="session", autouse=True)
def probe_bundle() -> None:
    dist = FIXTURE_ROOT.parents[1] / "packages" / "probe" / "dist"
    if not all((dist / f"{name}.js").is_file() for name in ("probe", "snapshot")):
        subprocess.run(
            ["pnpm", "--filter", "@clarity-compass/probe", "build"],
            cwd=FIXTURE_ROOT.parents[1],
            check=True,
            capture_output=True,
        )
