import ipaddress
import subprocess
import threading
from collections.abc import AsyncIterator, Iterator
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qsl

import pytest
from playwright.async_api import Browser, async_playwright

from clarity_core.net.guard import AddressGuard
from clarity_persistence.testing import database_url_for_tests, recreate_tables

FIXTURE_ROOT = Path(__file__).resolve().parents[3] / "fixtures" / "bugfarmcc"


LOGIN = {"email": "demo@bugfarm.test", "password": "correct-horse"}
PRIVATE = ("/account.html", "/account-saved.html")


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass

    def do_GET(self) -> None:
        if self.path.startswith(PRIVATE) and "session=ok" not in self.headers.get("Cookie", ""):
            self._redirect("/login.html")
            return
        if self.path.startswith("/logout"):
            self.send_response(303)
            self.send_header("Set-Cookie", "session=; Path=/; Max-Age=0")
            self.send_header("Location", "/")
            self.end_headers()
            return
        super().do_GET()

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        form = dict(parse_qsl(self.rfile.read(length).decode()))
        if self.path == "/session" and form == LOGIN:
            self.send_response(303)
            self.send_header("Set-Cookie", "session=ok; Path=/; HttpOnly")
            self.send_header("Location", "/account.html")
            self.end_headers()
            return
        self._redirect("/login.html?error=1")

    def _redirect(self, location: str) -> None:
        self.send_response(303)
        self.send_header("Location", location)
        self.end_headers()


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
    if not all((dist / f"{name}.js").is_file() for name in ("probe", "snapshot", "axe")):
        subprocess.run(
            ["pnpm", "--filter", "@clarity-compass/probe", "build"],
            cwd=FIXTURE_ROOT.parents[1],
            check=True,
            capture_output=True,
        )


@pytest.fixture
async def database_url() -> str:
    url = database_url_for_tests()
    if not url:
        pytest.skip("CLARITY_TEST_DATABASE_URL is not configured")
    await recreate_tables(url)
    return url
