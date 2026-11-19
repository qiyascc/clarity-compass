import contextlib
import time
from datetime import UTC, datetime

from playwright.async_api import ConsoleMessage, Page, Request, Response
from playwright.async_api import Error as PlaywrightError

from clarity_core.domain.capture import ConsoleEntry, PageCapture, RequestIssue, Section
from clarity_worker.browser import GuardedContext
from clarity_worker.probe import run_probe
from clarity_worker.store import ArtifactStore

MAX_FULL_PAGE_HEIGHT = 16_000


class CaptureError(Exception):
    pass


class _Recorder:
    def __init__(self, page: Page) -> None:
        self.console: list[ConsoleEntry] = []
        self.page_errors: list[str] = []
        self.request_issues: list[RequestIssue] = []
        page.on("console", self._on_console)
        page.on("pageerror", lambda error: self.page_errors.append(str(error)))
        page.on("requestfailed", self._on_failed)
        page.on("response", self._on_response)

    def _on_console(self, message: ConsoleMessage) -> None:
        location = message.location
        where = f"{location['url']}:{location['lineNumber']}" if location.get("url") else None
        self.console.append(ConsoleEntry(level=message.type, text=message.text, location=where))

    def _on_failed(self, request: Request) -> None:
        failure = request.failure or "failed"
        if "blockedbyclient" in failure.lower():
            return
        self.request_issues.append(
            RequestIssue(
                url=request.url,
                method=request.method,
                resource_type=request.resource_type,
                error=failure,
            )
        )

    def _on_response(self, response: Response) -> None:
        if response.status >= 400:
            request = response.request
            self.request_issues.append(
                RequestIssue(
                    url=response.url,
                    method=request.method,
                    resource_type=request.resource_type,
                    status=response.status,
                )
            )


class PageCapturer:
    def __init__(
        self,
        store: ArtifactStore,
        prefix: str,
        *,
        scroll_pause_ms: int = 250,
        max_scroll_steps: int = 60,
        navigation_timeout_ms: int = 30_000,
    ) -> None:
        self.store = store
        self.prefix = prefix.rstrip("/")
        self.scroll_pause_ms = scroll_pause_ms
        self.max_scroll_steps = max_scroll_steps
        self.navigation_timeout_ms = navigation_timeout_ms

    async def capture(self, guarded: GuardedContext, url: str) -> PageCapture:
        page = await guarded.new_page()
        recorder = _Recorder(page)
        started = time.monotonic()
        try:
            response = await page.goto(url, wait_until="load", timeout=self.navigation_timeout_ms)
        except PlaywrightError as exc:
            if guarded.blocked and guarded.blocked[-1].url.rstrip("/") == url.rstrip("/"):
                raise CaptureError(f"navigation blocked: {guarded.blocked[-1].error}") from exc
            raise CaptureError(f"navigation failed: {exc.message}") from exc
        await _settle_network(page)
        load_ms = int((time.monotonic() - started) * 1000)

        initial_height = await _document_height(page)
        await self._scroll_through(page)
        page_height = await _document_height(page)

        slug = f"{self.prefix}/{guarded.viewport.value}"
        probe = await run_probe(page)
        probe_key = await self.store.put(f"{slug}/probe.json", probe.model_dump_json().encode())
        sections = await self._sections(page, slug, page_height)
        full_page = await self._full_page(page, slug, page_height)
        links = await _links(page)
        title = await page.title()
        final_url = page.url
        await page.close()

        return PageCapture(
            requested_url=url,
            final_url=final_url,
            viewport=guarded.viewport,
            status=response.status if response else None,
            title=title,
            page_height=page_height,
            initial_height=initial_height,
            sections=sections,
            full_page=full_page,
            links=links,
            probe=probe_key,
            console=recorder.console,
            page_errors=recorder.page_errors,
            request_issues=recorder.request_issues,
            blocked_requests=list(guarded.blocked),
            load_ms=load_ms,
            captured_at=datetime.now(UTC),
        )

    async def _scroll_through(self, page: Page) -> None:
        step = _viewport_height(page)
        y = 0
        stable = 0
        for _ in range(self.max_scroll_steps):
            height = await _document_height(page)
            y = min(y + step, height)
            await page.evaluate("y => window.scrollTo(0, y)", y)
            await page.wait_for_timeout(self.scroll_pause_ms)
            if y + step >= await _document_height(page):
                stable += 1
                if stable >= 2:
                    break
            else:
                stable = 0
        await _settle_network(page)
        await page.evaluate("() => window.scrollTo(0, 0)")
        await page.wait_for_timeout(self.scroll_pause_ms)

    async def _sections(self, page: Page, slug: str, page_height: int) -> list[Section]:
        step = _viewport_height(page)
        sections: list[Section] = []
        offset = 0
        while offset < page_height:
            scroll_y = await page.evaluate(
                "y => { window.scrollTo(0, y); return Math.round(window.scrollY); }", offset
            )
            await page.wait_for_timeout(self.scroll_pause_ms)
            index = len(sections)
            shot = await page.screenshot(animations="disabled")
            key = await self.store.put(f"{slug}/section-{index:02d}.png", shot)
            visible = min(step, page_height - scroll_y)
            sections.append(Section(index=index, scroll_y=scroll_y, height=visible, screenshot=key))
            if scroll_y + step >= page_height:
                break
            offset = scroll_y + step
        if sections:
            last = sections[-1]
            sections[-1] = last.model_copy(update={"height": page_height - last.scroll_y})
        await page.evaluate("() => window.scrollTo(0, 0)")
        return sections

    async def _full_page(self, page: Page, slug: str, page_height: int) -> str | None:
        if page_height > MAX_FULL_PAGE_HEIGHT:
            return None
        shot = await page.screenshot(full_page=True, animations="disabled")
        return await self.store.put(f"{slug}/full.png", shot)


def _viewport_height(page: Page) -> int:
    size = page.viewport_size
    if size is None:
        raise CaptureError("page has no viewport")
    return size["height"]


async def _links(page: Page) -> list[str]:
    hrefs: list[str] = await page.evaluate(
        """() => [...new Set([...document.querySelectorAll('a[href]')]
            .map((a) => a.href)
            .filter((href) => href.startsWith('http')))]"""
    )
    return hrefs


async def _document_height(page: Page) -> int:
    height: int = await page.evaluate(
        "() => Math.max(document.documentElement.scrollHeight, document.body?.scrollHeight ?? 0)"
    )
    return height


async def _settle_network(page: Page, timeout_ms: int = 5_000) -> None:
    with contextlib.suppress(PlaywrightError):
        await page.wait_for_load_state("networkidle", timeout=timeout_ms)
