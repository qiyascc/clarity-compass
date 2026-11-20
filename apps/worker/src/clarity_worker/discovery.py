import contextlib
import heapq
import itertools
from dataclasses import dataclass, field
from fnmatch import fnmatch
from urllib.parse import urljoin, urlsplit

from clarity_core.net.urls import InvalidUrlError, normalize_url, site_key

SKIPPED_EXTENSIONS = frozenset(
    {
        ".pdf", ".zip", ".rar", ".7z", ".gz", ".exe", ".dmg", ".apk",
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".avif", ".ico",
        ".mp4", ".webm", ".mov", ".mp3", ".wav",
        ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".csv", ".xml", ".json",
    }
)  # fmt: skip

KEY_PAGE_HINTS = (
    "contact", "about", "login", "signin", "sign-in", "register", "signup", "sign-up",
    "account", "dashboard", "search", "pricing", "listing", "listings", "product",
    "products", "cart", "checkout", "elan", "elanlar", "iletisim", "hakkimizda", "giris",
)  # fmt: skip


@dataclass(order=True)
class _Entry:
    priority: tuple[int, int, int]
    url: str = field(compare=False)
    depth: int = field(compare=False)


@dataclass(frozen=True)
class FrontierItem:
    url: str
    depth: int


class Frontier:
    def __init__(
        self,
        start_url: str,
        *,
        max_pages: int,
        max_depth: int,
        exclude: list[str] | None = None,
    ) -> None:
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.exclude = exclude or []
        self._sites = {site_key(start_url)}
        self._seen: set[str] = set()
        self._depths: dict[str, int] = {}
        self._heap: list[_Entry] = []
        self._counter = itertools.count()
        self._popped = 0
        self._push(normalize_url(start_url), 0, rank=-1)

    @property
    def visited(self) -> int:
        return self._popped

    def adopt_host(self, url: str) -> None:
        self._sites.add(site_key(url))

    def mark_visited(self, url: str) -> None:
        with contextlib.suppress(InvalidUrlError):
            self._seen.add(_identity(normalize_url(url)))

    def add_seeds(self, urls: list[str]) -> None:
        for url in urls:
            self._consider(url, url, 0)

    def add_links(self, source_url: str, hrefs: list[str], depth: int | None = None) -> None:
        parent_depth = self._depth_of(source_url) if depth is None else depth
        for href in hrefs:
            self._consider(source_url, href, parent_depth + 1)

    def pop(self) -> FrontierItem | None:
        if self._popped >= self.max_pages or not self._heap:
            return None
        entry = heapq.heappop(self._heap)
        self._popped += 1
        return FrontierItem(entry.url, entry.depth)

    def _consider(self, base: str, href: str, depth: int) -> None:
        if depth > self.max_depth:
            return
        try:
            url = normalize_url(urljoin(base, href.strip()))
        except InvalidUrlError:
            return
        if site_key(url) not in self._sites:
            return
        path = urlsplit(url).path
        if _extension(path) in SKIPPED_EXTENSIONS:
            return
        if any(fnmatch(path, pattern) for pattern in self.exclude):
            return
        self._push(url, depth)

    def _push(self, url: str, depth: int, rank: int | None = None) -> None:
        identity = _identity(url)
        if identity in self._seen:
            return
        self._seen.add(identity)
        self._depths[identity] = depth
        if rank is None:
            rank = 0 if _is_key_page(url) else 1
        heapq.heappush(self._heap, _Entry((depth, rank, next(self._counter)), url, depth))

    def _depth_of(self, url: str) -> int:
        try:
            return self._depths.get(_identity(normalize_url(url)), 0)
        except InvalidUrlError:
            return 0


def _identity(url: str) -> str:
    parts = urlsplit(url)
    path = parts.path.rstrip("/") or "/"
    return f"{site_key(url)}{path}?{parts.query}"


def _extension(path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    return name[name.rfind(".") :].lower() if "." in name else ""


def _is_key_page(url: str) -> bool:
    segments = [segment.lower() for segment in urlsplit(url).path.split("/") if segment]
    return any(segment.split(".")[0] in KEY_PAGE_HINTS for segment in segments)
