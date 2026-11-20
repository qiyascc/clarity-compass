from collections.abc import Callable, Iterable
from dataclasses import dataclass
from urllib.parse import urlsplit

from clarity_core.domain.capture import PageCapture
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
from clarity_worker.checks.messages import VIEWPORT_NAMES, message

MAX_PER_RULE = 8
SLOW_LOAD_MS = 5_000
TAP_TARGET = 24
CONTROL_TAGS = {"button", "input", "select", "textarea", "summary"}
BLOCKING_RESOURCES = {"script", "stylesheet", "fetch", "xhr", "document", "font"}


@dataclass(frozen=True)
class Page:
    capture: PageCapture
    probe: PageProbe
    language: str
    primary: bool

    @property
    def viewport(self) -> Viewport:
        return self.capture.viewport

    def finding(
        self,
        rule: str,
        category: Category,
        severity: Severity,
        evidence: list[Evidence],
        anchor: ElementAnchor | None = None,
        **values: object,
    ) -> Finding:
        text = message(rule, self.language, **values)
        return Finding(
            page_url=self.capture.final_url,
            viewport=self.viewport,
            category=category,
            severity=severity,
            status=Status.VERIFIED,
            confidence=1.0,
            title=text.title,
            description=text.description,
            recommendation=text.recommendation,
            anchor=anchor,
            evidence=evidence,
            source=f"check:{rule}",
        )


Rule = Callable[[Page], Iterable[Finding]]


def anchor(element: ProbedElement) -> ElementAnchor:
    return ElementAnchor(
        selector=element.selector,
        xpath=element.xpath,
        text=element.name or element.text or None,
        role=element.role,
        box=element.box,
    )


def short(text: str, limit: int = 60) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else f"{text[: limit - 1]}…"


def _transparent(color: str | None) -> bool:
    if not color or not color.startswith("rgba("):
        return False
    try:
        return float(color.rstrip(")").rsplit(",", 1)[1]) < 0.1
    except (IndexError, ValueError):
        return False


def _visually_hidden(element: ProbedElement) -> bool:
    return element.box.width <= 2 or element.box.height <= 2


def _labelled_toggle(probe: PageProbe, element: ProbedElement) -> bool:
    return any(
        field.selector == element.selector and field.type in {"checkbox", "radio"} and field.label
        for form in probe.forms
        for field in form.fields
    )


def low_contrast(page: Page) -> Iterable[Finding]:
    found = 0
    seen: set[tuple[str | None, str | None, str]] = set()
    for element in page.probe.elements:
        if found >= MAX_PER_RULE:
            return
        if not element.visible or not element.text or element.contrast is None:
            continue
        if _transparent(element.color) or _visually_hidden(element):
            continue
        large = element.font_size >= 24 or (
            element.font_size >= 18.66 and element.font_weight >= 700
        )
        required = 3.0 if large else 4.5
        if element.contrast >= required:
            continue
        key = (element.color, element.background, element.text[:40])
        if key in seen:
            continue
        seen.add(key)
        found += 1
        severity = Severity.HIGH if element.contrast < 2 else Severity.MEDIUM
        if element.contrast >= 3:
            severity = Severity.LOW
        yield page.finding(
            "low-contrast",
            Category.ACCESSIBILITY,
            severity,
            [
                Evidence(
                    kind=EvidenceKind.METRIC,
                    ref=f"contrast {element.contrast:.2f}:1",
                    summary=f"{element.color} on {element.background}, {element.font_size:g}px",
                )
            ],
            anchor(element),
            text=short(element.text),
            color=element.color,
            background=element.background,
            ratio=f"{element.contrast:.2f}",
            required=f"{required:g}",
        )


def small_tap_targets(page: Page) -> Iterable[Finding]:
    if not page.viewport.is_mobile:
        return
    found = 0
    for element in page.probe.elements:
        if found >= MAX_PER_RULE:
            return
        if not (element.visible and element.interactive) or element.disabled:
            continue
        is_control = element.tag in CONTROL_TAGS or element.role == "button"
        compact_link = element.tag == "a" and element.box.width < 44
        if not (is_control or compact_link):
            continue
        box = element.box
        if min(box.width, box.height) >= TAP_TARGET or _visually_hidden(element):
            continue
        if element.tag == "input" and element.name and _labelled_toggle(page.probe, element):
            continue
        found += 1
        yield page.finding(
            "small-tap-target",
            Category.ACCESSIBILITY,
            Severity.MEDIUM,
            [
                Evidence(
                    kind=EvidenceKind.METRIC,
                    ref=f"{box.width:g}x{box.height:g}px",
                    summary=f"{page.viewport.value} viewport",
                )
            ],
            anchor(element),
            text=short(element.name or element.text or element.tag),
            width=f"{box.width:g}",
            height=f"{box.height:g}",
            viewport=VIEWPORT_NAMES.get(page.language, VIEWPORT_NAMES["en"])[page.viewport.value],
        )


def images(page: Page) -> Iterable[Finding]:
    failures = {issue.url: issue for issue in page.capture.request_issues}
    missing_alt = 0
    for image in page.probe.images:
        box = image.box
        target = ElementAnchor(selector=image.selector, box=box)
        name = short(urlsplit(image.src).path.rsplit("/", 1)[-1] or image.src, 40)
        failure = failures.get(image.src)
        if failure and not image.loaded:
            reason = f"HTTP {failure.status}" if failure.status else (failure.error or "failed")
            yield page.finding(
                "broken-image",
                Category.FUNCTIONAL,
                Severity.HIGH,
                [Evidence(kind=EvidenceKind.NETWORK, ref=f"GET {image.src}", summary=reason)],
                target,
                src=name,
                reason=reason,
            )
        if (
            image.alt is None
            and box.width >= 32
            and box.height >= 32
            and missing_alt < MAX_PER_RULE
        ):
            missing_alt += 1
            yield page.finding(
                "missing-alt",
                Category.ACCESSIBILITY,
                Severity.MEDIUM,
                [Evidence(kind=EvidenceKind.DOM, ref=image.selector, summary="img without alt")],
                target,
                src=name,
                width=f"{box.width:g}",
                height=f"{box.height:g}",
            )


def failed_resources(page: Page) -> Iterable[Finding]:
    if not page.primary:
        return
    failures = [
        issue
        for issue in page.capture.request_issues
        if issue.resource_type in BLOCKING_RESOURCES and issue.url != page.capture.final_url
    ]
    if not failures:
        return
    items = ", ".join(
        f"{short(urlsplit(i.url).path, 40)} ({i.status or i.error})" for i in failures[:4]
    )
    severity = (
        Severity.HIGH
        if any(i.resource_type in {"script", "stylesheet"} for i in failures)
        else Severity.MEDIUM
    )
    yield page.finding(
        "failed-resource",
        Category.FUNCTIONAL,
        severity,
        [
            Evidence(
                kind=EvidenceKind.NETWORK,
                ref=f"{i.method} {i.url}",
                summary=str(i.status or i.error),
            )
            for i in failures[:10]
        ],
        count=len(failures),
        items=items,
    )


def console_errors(page: Page) -> Iterable[Finding]:
    if not page.primary:
        return
    errors = [entry.text for entry in page.capture.console if entry.level == "error"]
    errors += page.capture.page_errors
    errors = [error for error in errors if "Failed to load resource" not in error]
    if not errors:
        return
    yield page.finding(
        "console-errors",
        Category.FUNCTIONAL,
        Severity.HIGH if page.capture.page_errors else Severity.MEDIUM,
        [Evidence(kind=EvidenceKind.CONSOLE, ref=short(error, 200)) for error in errors[:10]],
        count=len(errors),
        items="; ".join(f"“{short(error, 80)}”" for error in errors[:3]),
    )


def error_status(page: Page) -> Iterable[Finding]:
    status = page.capture.status
    if not page.primary or status is None or status < 400:
        return
    yield page.finding(
        "error-status",
        Category.FUNCTIONAL,
        Severity.CRITICAL,
        [
            Evidence(
                kind=EvidenceKind.NETWORK,
                ref=f"GET {page.capture.requested_url}",
                summary=str(status),
            )
        ],
        status=status,
        url=page.capture.requested_url,
    )


def document_basics(page: Page) -> Iterable[Finding]:
    if not page.primary:
        return
    probe = page.probe
    if not probe.lang:
        yield page.finding(
            "missing-lang",
            Category.ACCESSIBILITY,
            Severity.LOW,
            [Evidence(kind=EvidenceKind.DOM, ref="html", summary="no lang attribute")],
            suggested=page.language,
        )
    first_level = [heading for heading in probe.headings if heading.level == 1]
    if not first_level and (page.capture.status or 200) < 400:
        yield page.finding(
            "no-h1",
            Category.ACCESSIBILITY,
            Severity.MEDIUM,
            [Evidence(kind=EvidenceKind.DOM, ref="h1", summary="0 elements")],
        )
    elif len(first_level) > 1:
        yield page.finding(
            "multiple-h1",
            Category.CONTENT,
            Severity.LOW,
            [Evidence(kind=EvidenceKind.DOM, ref=h.selector, summary=h.text) for h in first_level],
            ElementAnchor(selector=first_level[1].selector, text=first_level[1].text),
            count=len(first_level),
            items=", ".join(f"“{short(h.text, 40)}”" for h in first_level[:3]),
        )


def mobile_viewport(page: Page) -> Iterable[Finding]:
    if page.viewport is Viewport.MOBILE and not page.probe.viewport_meta:
        yield page.finding(
            "missing-viewport",
            Category.UX,
            Severity.HIGH,
            [Evidence(kind=EvidenceKind.DOM, ref='meta[name="viewport"]', summary="missing")],
        )


def horizontal_overflow(page: Page) -> Iterable[Finding]:
    probe = page.probe
    screen = page.viewport.width
    if not page.viewport.is_mobile or probe.document_width <= screen + 2:
        return
    culprit = probe.overflowing[0] if probe.overflowing else "html"
    yield page.finding(
        "horizontal-overflow",
        Category.UX,
        Severity.HIGH,
        [
            Evidence(
                kind=EvidenceKind.METRIC,
                ref=f"scrollWidth {probe.document_width}px > {screen}px",
                summary=", ".join(probe.overflowing),
            )
        ],
        ElementAnchor(selector=culprit) if probe.overflowing else None,
        viewport=VIEWPORT_NAMES.get(page.language, VIEWPORT_NAMES["en"])[page.viewport.value],
        width=probe.document_width,
        screen=screen,
        culprit=culprit,
    )


def slow_load(page: Page) -> Iterable[Finding]:
    if page.capture.load_ms < SLOW_LOAD_MS:
        return
    yield page.finding(
        "slow-load",
        Category.PERFORMANCE,
        Severity.HIGH if page.capture.load_ms >= 2 * SLOW_LOAD_MS else Severity.MEDIUM,
        [Evidence(kind=EvidenceKind.METRIC, ref=f"load {page.capture.load_ms} ms")],
        seconds=f"{page.capture.load_ms / 1000:.1f}",
        viewport=VIEWPORT_NAMES.get(page.language, VIEWPORT_NAMES["en"])[page.viewport.value],
    )


RULES: tuple[Rule, ...] = (
    error_status,
    console_errors,
    failed_resources,
    images,
    low_contrast,
    small_tap_targets,
    mobile_viewport,
    horizontal_overflow,
    document_basics,
    slow_load,
)
