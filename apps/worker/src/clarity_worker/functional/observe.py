from dataclasses import dataclass, field

from playwright.async_api import ConsoleMessage, Page, Request

WATCH = """() => {
  if (window.__clarityWatch) return;
  const watch = { mutations: 0 };
  new MutationObserver((records) => { watch.mutations += records.length; })
    .observe(document.documentElement, {
      subtree: true, childList: true, attributes: true, characterData: true,
    });
  window.__clarityWatch = watch;
}"""

SNAPSHOT = """(selector) => {
  const visible = (el) => {
    const style = getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden') return false;
    if (Number(style.opacity) < 0.05 || /100%/.test(style.clipPath)) return false;
    if (el.closest('[aria-hidden=true], [inert]')) return false;
    const rect = el.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0 && rect.bottom > 0 && rect.right > 0
      && rect.top < innerHeight && rect.left < innerWidth;
  };
  const modal = 'dialog[open], [role=dialog], [role=alertdialog], [aria-modal=true]';
  const dialogs = [...document.querySelectorAll(modal)].filter(visible).length;
  const target = selector ? document.querySelector(selector) : null;
  const text = (document.body?.innerText ?? '').replace(/\\s+/g, ' ').trim();
  return {
    url: location.href,
    scrollY: Math.round(window.scrollY),
    mutations: window.__clarityWatch?.mutations ?? 0,
    dialogs,
    expanded: target?.getAttribute('aria-expanded') ?? null,
    lang: document.documentElement.getAttribute('lang'),
    words: text.split(' ').slice(0, 1500),
    active: document.activeElement?.tagName ?? null,
  };
}"""


@dataclass(frozen=True)
class Snapshot:
    url: str
    scroll_y: int
    mutations: int
    dialogs: int
    expanded: str | None
    lang: str | None
    words: list[str]
    active: str | None


@dataclass
class Activity:
    requests: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    popups: int = 0


class PageWatcher:
    """Keeps a running record of what a page does so actions can be compared."""

    def __init__(self, page: Page) -> None:
        self.page = page
        self.activity = Activity()
        page.on("request", self._on_request)
        page.on("console", self._on_console)
        page.on("pageerror", lambda error: self.activity.errors.append(str(error)))
        page.on("popup", self._on_popup)

    async def install(self) -> None:
        await self.page.evaluate(WATCH)

    async def snapshot(self, selector: str | None = None) -> Snapshot:
        await self.install()
        raw = await self.page.evaluate(SNAPSHOT, selector)
        return Snapshot(
            url=raw["url"],
            scroll_y=raw["scrollY"],
            mutations=raw["mutations"],
            dialogs=raw["dialogs"],
            expanded=raw["expanded"],
            lang=raw["lang"],
            words=raw["words"],
            active=raw["active"],
        )

    def mark(self) -> Activity:
        current = self.activity
        self.activity = Activity()
        return current

    def _on_request(self, request: Request) -> None:
        if request.resource_type in {"document", "xhr", "fetch", "script"}:
            self.activity.requests.append(f"{request.method} {request.url}")

    def _on_console(self, message: ConsoleMessage) -> None:
        if message.type == "error" and "Failed to load resource" not in message.text:
            self.activity.errors.append(message.text)

    def _on_popup(self, popup: Page) -> None:
        self.activity.popups += 1


def changed_share(before: list[str], after: list[str]) -> float:
    if not before and not after:
        return 0.0
    longest = max(len(before), len(after))
    same = sum(1 for a, b in zip(before, after, strict=False) if a == b)
    return 1 - same / longest
