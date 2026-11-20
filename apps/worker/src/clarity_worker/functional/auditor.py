import asyncio
import contextlib
import json
import re
from dataclasses import asdict, dataclass, field
from urllib.parse import urldefrag

from playwright.async_api import APIRequestContext, Page
from playwright.async_api import Error as PlaywrightError

from clarity_core.domain.findings import (
    Category,
    ElementAnchor,
    Evidence,
    EvidenceKind,
    Finding,
    Severity,
    Status,
)
from clarity_core.domain.probe import PageProbe, ProbedElement
from clarity_core.domain.viewport import Viewport
from clarity_core.net.guard import AddressGuard, UnsafeTargetError
from clarity_core.net.urls import same_site
from clarity_worker.browser import GuardedContext
from clarity_worker.checks.messages import message
from clarity_worker.functional.guard import Risk, classify
from clarity_worker.functional.observe import PageWatcher, Snapshot, changed_share
from clarity_worker.probe import run_probe
from clarity_worker.store import ArtifactStore

TARGET_EXISTS = "(id) => Boolean(document.getElementById(id) || document.getElementsByName(id)[0])"
SETTLE_MS = 700
CLICK_TIMEOUT_MS = 3_000
MAX_LINK_CHECKS = 40
LANGUAGE_LABEL = re.compile(
    r"^(en|eng|english|tr|türkçe|turkish|az|aze|azərbaycan(ca)?|ru|rus|русский|de|fr|es)$",
    re.IGNORECASE,
)
TOGGLE_HINT = re.compile(r"(menu|menyu|меню|nav|burger|toggle|filter|filtr|фильтр|more|daha)", re.I)
CLOSE_BUTTON = (
    "[aria-label*=close i], [aria-label*=bağla i], [aria-label*=kapat i], "
    "[aria-label*=закрыть i], .close, .modal-close, [data-dismiss], [data-bs-dismiss]"
)


@dataclass
class Step:
    action: str
    observation: dict[str, object] = field(default_factory=dict)


@dataclass
class Trace:
    page_url: str
    viewport: str
    selector: str
    label: str
    steps: list[Step] = field(default_factory=list)

    def note(self, action: str, **observation: object) -> None:
        self.steps.append(Step(action, observation))


@dataclass
class Outcome:
    before: Snapshot
    after: Snapshot
    requests: list[str]
    errors: list[str]
    popups: int

    @property
    def navigated(self) -> bool:
        return urldefrag(self.before.url)[0] != urldefrag(self.after.url)[0]

    @property
    def visible_effect(self) -> bool:
        return (
            self.navigated
            or self.before.url != self.after.url
            or self.after.mutations > self.before.mutations
            or abs(self.after.scroll_y - self.before.scroll_y) > 2
            or self.after.dialogs != self.before.dialogs
            or self.after.expanded != self.before.expanded
            or bool(self.requests)
            or self.popups > 0
        )

    def summary(self) -> dict[str, object]:
        return {
            "url": self.after.url,
            "navigated": self.navigated,
            "dom_changes": self.after.mutations - self.before.mutations,
            "scroll": [self.before.scroll_y, self.after.scroll_y],
            "dialogs": [self.before.dialogs, self.after.dialogs],
            "expanded": [self.before.expanded, self.after.expanded],
            "requests": self.requests[:10],
            "errors": self.errors[:5],
            "popups": self.popups,
        }


class FunctionalAuditor:
    """Exercises a page the way a cautious visitor would and reports what fails.

    Every finding comes from an interaction that was performed and observed;
    each one carries the trace of that interaction as evidence.
    """

    def __init__(
        self,
        store: ArtifactStore,
        guard: AddressGuard,
        *,
        language: str,
        max_actions: int,
        prefix: str,
    ) -> None:
        self.store = store
        self.guard = guard
        self.language = language
        self.max_actions = max_actions
        self.prefix = prefix.rstrip("/")
        self._traces = 0

    async def audit(self, context: GuardedContext, url: str) -> list[Finding]:
        page = await context.new_page()
        watcher = PageWatcher(page)
        try:
            await self._open(page, url)
            probe = await run_probe(page)
            findings = await self._links(context.context.request, probe, context.viewport)
            findings += await self._anchors(page, watcher, probe, context.viewport)
            findings += await self._controls(page, watcher, probe, url, context.viewport)
            return findings
        finally:
            await page.close()

    async def _open(self, page: Page, url: str) -> None:
        await page.goto(url, wait_until="load", timeout=30_000)
        with contextlib.suppress(PlaywrightError):
            await page.wait_for_load_state("networkidle", timeout=4_000)

    async def _links(
        self, request: APIRequestContext, probe: PageProbe, viewport: Viewport
    ) -> list[Finding]:
        targets: dict[str, ProbedElement] = {}
        for element in probe.elements:
            href = element.href
            if not href or element.tag != "a" or classify(element) is Risk.FORBIDDEN:
                continue
            target = urldefrag(href)[0]
            if not target.startswith("http") or not same_site(target, probe.url):
                continue
            if urldefrag(probe.url)[0] == target:
                continue
            targets.setdefault(target, element)

        async def status_of(target: str) -> tuple[str, int | None]:
            try:
                await self.guard.check_url(target)
                response = await request.get(target, timeout=15_000, max_redirects=5)
            except (UnsafeTargetError, PlaywrightError):
                return target, None
            return target, response.status

        results = await asyncio.gather(
            *(status_of(target) for target in list(targets)[:MAX_LINK_CHECKS])
        )
        findings = []
        for target, status in results:
            if status is None or status < 400:
                continue
            element = targets[target]
            trace = Trace(probe.url, viewport.value, element.selector, element.name)
            trace.note("request", url=target, status=status)
            findings.append(
                await self._finding(
                    "broken-link",
                    Severity.HIGH,
                    element,
                    trace,
                    probe.url,
                    viewport,
                    extra=[
                        Evidence(
                            kind=EvidenceKind.NETWORK, ref=f"GET {target}", summary=str(status)
                        )
                    ],
                    text=_label(element),
                    url=target,
                    status=status,
                )
            )
        return findings

    async def _anchors(
        self, page: Page, watcher: PageWatcher, probe: PageProbe, viewport: Viewport
    ) -> list[Finding]:
        findings = []
        for element in probe.elements:
            href = element.href or ""
            base, fragment = urldefrag(href)
            if not fragment or base != urldefrag(probe.url)[0] or not element.visible:
                continue
            exists = await page.evaluate(TARGET_EXISTS, fragment)
            if exists:
                continue
            trace = Trace(probe.url, viewport.value, element.selector, element.name)
            trace.note("lookup", target=fragment, found=False)
            outcome = await self._click(page, watcher, element, trace)
            if outcome and abs(outcome.after.scroll_y - outcome.before.scroll_y) <= 2:
                findings.append(
                    await self._finding(
                        "anchor-missing",
                        Severity.MEDIUM,
                        element,
                        trace,
                        probe.url,
                        viewport,
                        text=_label(element),
                        target=fragment,
                    )
                )
        return findings

    async def _controls(
        self,
        page: Page,
        watcher: PageWatcher,
        probe: PageProbe,
        url: str,
        viewport: Viewport,
    ) -> list[Finding]:
        findings: list[Finding] = []
        actions = 0
        for element in _controls(probe):
            if actions >= self.max_actions:
                break
            if viewport.is_mobile and not _looks_like_toggle(element):
                continue
            actions += 1
            trace = Trace(probe.url, viewport.value, element.selector, element.name)
            outcome = await self._click(page, watcher, element, trace)
            if outcome is None:
                continue

            if outcome.errors:
                findings.append(
                    await self._finding(
                        "click-error",
                        Severity.HIGH,
                        element,
                        trace,
                        probe.url,
                        viewport,
                        extra=[Evidence(kind=EvidenceKind.CONSOLE, ref=outcome.errors[0][:300])],
                        text=_label(element),
                        error=outcome.errors[0][:160],
                    )
                )
            elif not outcome.visible_effect:
                findings.append(
                    await self._finding(
                        "no-effect",
                        Severity.HIGH,
                        element,
                        trace,
                        probe.url,
                        viewport,
                        text=_label(element),
                    )
                )
            elif _is_language_switch(element) and not outcome.navigated:
                share = changed_share(outcome.before.words, outcome.after.words)
                if share < 0.05 and outcome.after.lang == outcome.before.lang:
                    findings.append(
                        await self._finding(
                            "language-partial",
                            Severity.MEDIUM,
                            element,
                            trace,
                            probe.url,
                            viewport,
                            text=_label(element),
                            changed=f"{share * 100:.0f}",
                            lang=outcome.after.lang or "unset",
                        )
                    )
            elif outcome.after.dialogs > outcome.before.dialogs:
                if not await self._dismiss_dialog(page, watcher, trace):
                    findings.append(
                        await self._finding(
                            "dialog-no-close",
                            Severity.HIGH,
                            element,
                            trace,
                            probe.url,
                            viewport,
                            text=_label(element),
                        )
                    )
            elif (
                outcome.after.expanded == "true" or _looks_like_toggle(element)
            ) and not await self._closes_again(page, watcher, element, trace, outcome):
                findings.append(
                    await self._finding(
                        "menu-no-close",
                        Severity.MEDIUM,
                        element,
                        trace,
                        probe.url,
                        viewport,
                        text=_label(element),
                    )
                )

            if outcome.visible_effect or outcome.errors:
                await self._open(page, url)
                watcher.mark()
        return findings

    async def _click(
        self, page: Page, watcher: PageWatcher, element: ProbedElement, trace: Trace
    ) -> Outcome | None:
        locator = page.locator(element.selector).first
        try:
            await locator.scroll_into_view_if_needed(timeout=CLICK_TIMEOUT_MS)
            await page.wait_for_timeout(150)
            before = await watcher.snapshot(element.selector)
            watcher.mark()
            await locator.click(timeout=CLICK_TIMEOUT_MS, no_wait_after=True)
            await page.wait_for_timeout(SETTLE_MS)
            after = await watcher.snapshot(element.selector)
        except PlaywrightError as exc:
            trace.note("click", skipped=str(exc).splitlines()[0][:200])
            return None
        activity = watcher.mark()
        outcome = Outcome(before, after, activity.requests, activity.errors, activity.popups)
        trace.note("click", **outcome.summary())
        return outcome

    async def _dismiss_dialog(self, page: Page, watcher: PageWatcher, trace: Trace) -> bool:
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(400)
        state = await watcher.snapshot()
        trace.note("press Escape", dialogs=state.dialogs)
        if state.dialogs == 0:
            return True
        close = page.locator(CLOSE_BUTTON).filter(visible=True).first
        try:
            await close.click(timeout=1_500)
        except PlaywrightError:
            trace.note("click close button", found=False)
            return False
        await page.wait_for_timeout(400)
        state = await watcher.snapshot()
        trace.note("click close button", dialogs=state.dialogs)
        return state.dialogs == 0

    async def _closes_again(
        self,
        page: Page,
        watcher: PageWatcher,
        element: ProbedElement,
        trace: Trace,
        opened: Outcome,
    ) -> bool:
        if opened.navigated:
            return True
        second = await self._click(page, watcher, element, trace)
        if second is None:
            return True
        if second.after.expanded is not None:
            if second.after.expanded == "false":
                return True
        elif second.visible_effect:
            return True
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(400)
        state = await watcher.snapshot(element.selector)
        trace.note("press Escape", expanded=state.expanded)
        return state.expanded in (None, "false") and state.mutations > second.after.mutations

    async def _finding(
        self,
        rule: str,
        severity: Severity,
        element: ProbedElement,
        trace: Trace,
        page_url: str,
        viewport: Viewport,
        extra: list[Evidence] | None = None,
        **values: object,
    ) -> Finding:
        self._traces += 1
        key = await self.store.put(
            f"{self.prefix}/{viewport.value}/actions/{self._traces:03d}.json",
            json.dumps(asdict(trace), ensure_ascii=False, indent=1).encode(),
        )
        text = message(rule, self.language, **values)
        steps = " → ".join(step.action for step in trace.steps)
        return Finding(
            page_url=page_url,
            viewport=viewport,
            category=Category.FUNCTIONAL,
            severity=severity,
            status=Status.VERIFIED,
            confidence=0.95,
            title=text.title,
            description=text.description,
            recommendation=text.recommendation,
            anchor=ElementAnchor(
                selector=element.selector,
                xpath=element.xpath,
                text=element.name or element.text or None,
                role=element.role,
                box=element.box,
            ),
            evidence=[
                Evidence(kind=EvidenceKind.ACTION_TRACE, ref=key, summary=steps),
                *(extra or []),
            ],
            source=f"functional:{rule}",
        )


def _controls(probe: PageProbe) -> list[ProbedElement]:
    chosen = []
    for element in probe.elements:
        if not (element.visible and element.interactive) or (element.tag == "a" and element.href):
            continue
        if element.tag in {"input", "select", "textarea"} and element.role not in {"button"}:
            continue
        if classify(element) is Risk.FORBIDDEN:
            continue
        chosen.append(element)
    return chosen


def _looks_like_toggle(element: ProbedElement) -> bool:
    return bool(TOGGLE_HINT.search(f"{element.name} {element.selector}")) or not element.name


def _is_language_switch(element: ProbedElement) -> bool:
    return bool(LANGUAGE_LABEL.match((element.name or element.text).strip()))


def _label(element: ProbedElement) -> str:
    text = " ".join((element.name or element.text or element.tag).split())
    return text if len(text) <= 60 else f"{text[:59]}…"
