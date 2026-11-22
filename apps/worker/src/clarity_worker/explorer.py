import hashlib
import re
from collections.abc import Awaitable, Callable
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlsplit

from playwright._impl._api_structures import SetCookieParam
from playwright.async_api import APIRequestContext, Browser, Cookie
from playwright.async_api import Error as PlaywrightError

from clarity_core.domain.capture import PageCapture
from clarity_core.domain.profile import AnalysisProfile, ScopeMode
from clarity_core.net.guard import AddressGuard, UnsafeTargetError
from clarity_worker.browser import GuardedContext, open_context
from clarity_worker.capture import CaptureError, PageCapturer
from clarity_worker.discovery import Frontier
from clarity_worker.policy import RequestPolicy
from clarity_worker.sitemap import parse_robots, parse_sitemap
from clarity_worker.store import ArtifactStore

PageCallback = Callable[[PageCapture], Awaitable[None]]
Prepare = Callable[[GuardedContext], Awaitable[str | None]]

MAX_SITEMAPS = 5
MAX_REDIRECTS = 3


@dataclass
class CaptureFailure:
    url: str
    viewport: str
    reason: str


@dataclass
class Exploration:
    pages: list[PageCapture] = field(default_factory=list)
    failures: list[CaptureFailure] = field(default_factory=list)


class SiteExplorer:
    def __init__(
        self,
        browser: Browser,
        store: ArtifactStore,
        guard: AddressGuard,
        *,
        scroll_pause_ms: int = 250,
    ) -> None:
        self.browser = browser
        self.store = store
        self.guard = guard
        self.scroll_pause_ms = scroll_pause_ms

    async def explore(
        self,
        profile: AnalysisProfile,
        run_id: str,
        on_page: PageCallback | None = None,
        prepare: Prepare | None = None,
    ) -> Exploration:
        frontier = _frontier_for(profile)
        result = Exploration()
        follow_links = profile.scope is ScopeMode.SITE

        async with AsyncExitStack() as stack:
            contexts = [
                await stack.enter_async_context(
                    open_context(self.browser, viewport, RequestPolicy(self.guard))
                )
                for viewport in profile.viewports
            ]
            primary = contexts[0]
            if prepare:
                # Sites that allow one session per account sign out earlier logins,
                # so sign in once and hand the session to the other viewports.
                landing = await prepare(primary)
                if landing:
                    cookies = _settable(await primary.context.cookies())
                    for context in contexts[1:]:
                        await context.context.add_cookies(cookies)
                    if follow_links:
                        frontier.add_links(profile.start_url, [landing], depth=0)
            sitemap_checked = not follow_links

            while (item := frontier.pop()) is not None:
                captures = await self._capture_everywhere(contexts, item.url, run_id, result)
                for capture in captures:
                    result.pages.append(capture)
                    if on_page:
                        await on_page(capture)
                if not captures or not follow_links:
                    continue

                lead = captures[0]
                frontier.adopt_host(lead.final_url)
                frontier.mark_visited(lead.final_url)
                if not sitemap_checked:
                    sitemap_checked = True
                    pages = await self._sitemap_pages(primary, lead.final_url)
                    frontier.add_links(lead.final_url, pages, depth=0)
                frontier.add_links(item.url, lead.links, depth=item.depth)

        return result

    async def _capture_everywhere(
        self,
        contexts: list[GuardedContext],
        url: str,
        run_id: str,
        result: Exploration,
    ) -> list[PageCapture]:
        capturer = PageCapturer(
            self.store, prefix=f"{run_id}/{_slug(url)}", scroll_pause_ms=self.scroll_pause_ms
        )
        captures = []
        for context in contexts:
            try:
                captures.append(await capturer.capture(context, url))
            except CaptureError as exc:
                result.failures.append(CaptureFailure(url, context.viewport.value, str(exc)))
        return captures

    async def _sitemap_pages(self, context: GuardedContext, site_url: str) -> list[str]:
        origin = "{0.scheme}://{0.netloc}".format(urlsplit(site_url))
        request = context.context.request
        robots = await self._fetch(request, f"{origin}/robots.txt")
        queue = parse_robots(robots.decode(errors="replace"), origin) if robots else []
        queue.append(f"{origin}/sitemap.xml")

        pages: list[str] = []
        seen: set[str] = set()
        while queue and len(seen) < MAX_SITEMAPS:
            sitemap_url = queue.pop(0)
            if sitemap_url in seen:
                continue
            seen.add(sitemap_url)
            content = await self._fetch(request, sitemap_url)
            if content:
                entries = parse_sitemap(content, sitemap_url)
                pages.extend(entries.pages)
                queue.extend(entries.sitemaps)
        return pages

    async def _fetch(self, request: APIRequestContext, url: str) -> bytes | None:
        for _ in range(MAX_REDIRECTS + 1):
            try:
                await self.guard.check_url(url)
                response = await request.get(url, max_redirects=0, timeout=10_000)
            except (UnsafeTargetError, PlaywrightError):
                return None
            if 300 <= response.status < 400 and "location" in response.headers:
                url = urljoin(url, response.headers["location"])
                continue
            return await response.body() if response.ok else None
        return None


def _frontier_for(profile: AnalysisProfile) -> Frontier:
    seeds = profile.seed_urls()
    frontier = Frontier(
        seeds[0],
        max_pages=profile.limits.max_pages if profile.scope is ScopeMode.SITE else len(seeds),
        max_depth=profile.limits.max_depth,
        exclude=profile.exclude_patterns,
    )
    frontier.add_seeds(seeds[1:])
    return frontier


def _slug(url: str) -> str:
    path = urlsplit(url).path.strip("/") or "home"
    readable = re.sub(r"[^a-zA-Z0-9]+", "-", path)[:48].strip("-")
    digest = hashlib.sha1(url.encode()).hexdigest()[:8]
    return f"{readable}-{digest}"


def _settable(cookies: list[Cookie]) -> list[SetCookieParam]:
    return [
        SetCookieParam(
            name=c["name"],
            value=c["value"],
            domain=c["domain"],
            path=c["path"],
            expires=c["expires"],
            httpOnly=c["httpOnly"],
            secure=c["secure"],
            sameSite=c["sameSite"],
        )
        for c in cookies
    ]
