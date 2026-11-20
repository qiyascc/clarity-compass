import asyncio
import io
from dataclasses import dataclass, field

from PIL import Image

from clarity_ai.agents import DesignReviewAgent, UnderstandingAgent
from clarity_ai.context import ElementLine, PageContext, Shot
from clarity_ai.provider import LLMProvider
from clarity_ai.schemas import DesignReview, PageUnderstanding, ReviewNote
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
from clarity_core.domain.prediction import ElementPrediction, PagePrediction
from clarity_core.domain.probe import PageProbe, ProbedElement
from clarity_core.domain.viewport import Viewport
from clarity_worker.store import ArtifactStore

MAX_ELEMENTS = {Viewport.DESKTOP: 110, Viewport.TABLET: 40, Viewport.MOBILE: 50}
MAX_SHOTS = {Viewport.DESKTOP: 4, Viewport.TABLET: 2, Viewport.MOBILE: 3}
SHOT_WIDTH = {Viewport.DESKTOP: 1024, Viewport.TABLET: 600, Viewport.MOBILE: 420}
HEADINGS = {"h1", "h2", "h3"}


@dataclass(frozen=True)
class CapturedView:
    capture: PageCapture
    probe: PageProbe
    prediction: PagePrediction | None


@dataclass
class PageReview:
    understanding: PageUnderstanding
    review: DesignReview
    findings: list[Finding]
    model: str


@dataclass
class _Built:
    context: PageContext
    elements: dict[int, tuple[Viewport, ProbedElement]] = field(default_factory=dict)


class PageReviewer:
    def __init__(self, provider: LLMProvider, store: ArtifactStore) -> None:
        self.understanding = UnderstandingAgent(provider)
        self.designer = DesignReviewAgent(provider)
        self.store = store

    async def review(self, views: list[CapturedView], language: str) -> PageReview:
        built = await build_context(views, language, self.store)
        understanding = await self.understanding.run(built.context)
        review = await self.designer.run(built.context, understanding.value)
        lead = views[0].capture
        findings = [to_finding(note, built.elements, lead, views) for note in review.value.notes]
        return PageReview(understanding.value, review.value, findings, review.model)


async def build_context(views: list[CapturedView], language: str, store: ArtifactStore) -> _Built:
    lead = views[0]
    context = PageContext(
        url=lead.capture.final_url,
        title=lead.capture.title,
        notes_language=language,
        headings=[f"h{h.level}: {h.text}" for h in lead.probe.headings if h.text],
    )
    built = _Built(context)
    number = 1
    for view in views:
        viewport = view.capture.viewport
        predicted = {e.index: e for e in (view.prediction.elements if view.prediction else [])}
        for element in _worth_describing(view.probe)[: MAX_ELEMENTS[viewport]]:
            context.elements.append(_line(number, viewport, element, predicted.get(element.index)))
            built.elements[number] = (viewport, element)
            number += 1
        for section in view.capture.sections[: MAX_SHOTS[viewport]]:
            raw = await store.get(section.screenshot)
            label = (
                f"{viewport.value} section {section.index + 1} "
                f"(document y {section.scroll_y}-{section.scroll_y + viewport.height})"
            )
            data = await asyncio.to_thread(_jpeg, raw, SHOT_WIDTH[viewport])
            context.shots.append(Shot(label, data))
        context.signals.extend(_signals(view))
    return built


def to_finding(
    note: ReviewNote,
    elements: dict[int, tuple[Viewport, ProbedElement]],
    lead: PageCapture,
    views: list[CapturedView],
) -> Finding:
    located = elements.get(note.element) if note.element is not None else None
    if located:
        viewport, element = located
        anchor: ElementAnchor | None = ElementAnchor(
            selector=element.selector,
            xpath=element.xpath,
            text=element.name or element.text or None,
            role=element.role,
            box=element.box,
        )
    else:
        captured = {view.capture.viewport for view in views}
        wanted = Viewport(note.viewport) if note.viewport != "all" else lead.viewport
        viewport = wanted if wanted in captured else lead.viewport
        anchor = None
    return Finding(
        page_url=lead.final_url,
        viewport=viewport,
        category=Category(note.category),
        severity=Severity(note.severity),
        status=Status.PREDICTED,
        confidence=min(1.0, max(0.0, note.confidence)),
        title=note.title[:200],
        description=note.description,
        recommendation=note.recommendation,
        alternative=note.alternative,
        anchor=anchor,
        evidence=[Evidence(kind=EvidenceKind.SCREENSHOT, ref="review", summary=note.evidence)],
        source="agent:ux-designer",
    )


def _worth_describing(probe: PageProbe) -> list[ProbedElement]:
    chosen = []
    for element in probe.elements:
        if not element.visible:
            continue
        low_contrast = element.contrast is not None and element.contrast < 4.5 and element.text
        if element.interactive or element.tag in HEADINGS or low_contrast:
            chosen.append(element)
    return chosen


def _line(
    number: int,
    viewport: Viewport,
    element: ProbedElement,
    predicted: ElementPrediction | None,
) -> ElementLine:
    box = element.box
    return ElementLine(
        number=number,
        viewport=viewport.value,
        tag=element.tag,
        role=element.role,
        name=element.name or element.text,
        x=round(box.x),
        y=round(box.y),
        width=round(box.width),
        height=round(box.height),
        fixed=element.position in {"fixed", "sticky"},
        font_size=element.font_size or None,
        contrast=element.contrast,
        attention=predicted.attention if predicted else None,
        click=predicted.click if predicted else None,
    )


def _signals(view: CapturedView) -> list[str]:
    capture = view.capture
    name = capture.viewport.value
    signals = [
        f"{name}: document {capture.page_height}px tall, {len(capture.sections)} screens, "
        f"loaded in {capture.load_ms} ms, HTTP {capture.status}",
    ]
    errors = sum(1 for entry in capture.console if entry.level == "error") + len(
        capture.page_errors
    )
    if errors:
        signals.append(f"{name}: {errors} JavaScript errors while loading")
    if capture.request_issues:
        signals.append(f"{name}: {len(capture.request_issues)} failed requests")
    if view.prediction:
        signals.append(f"{name}: attention models agree at {view.prediction.agreement:.2f}")
    return signals


def _jpeg(raw: bytes, width: int) -> bytes:
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    if image.width > width:
        image = image.resize(
            (width, round(image.height * width / image.width)), Image.Resampling.LANCZOS
        )
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=72, optimize=True)
    return buffer.getvalue()
