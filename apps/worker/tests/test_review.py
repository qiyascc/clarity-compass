import io
from pathlib import Path
from typing import Any

from PIL import Image
from playwright.async_api import Browser
from pydantic import BaseModel

from clarity_ai.provider import Generated, Prompt, Text
from clarity_ai.provider import Image as ImagePart
from clarity_ai.schemas import DesignReview, PageKind, PageUnderstanding, ReviewNote, Scores
from clarity_core.domain.findings import Status
from clarity_core.domain.probe import PageProbe
from clarity_core.domain.viewport import Viewport
from clarity_core.net.guard import AddressGuard
from clarity_worker.browser import open_context
from clarity_worker.capture import PageCapturer
from clarity_worker.policy import RequestPolicy
from clarity_worker.review import CapturedView, PageReviewer
from clarity_worker.store import LocalArtifactStore


class ScriptedProvider:
    name = "scripted"
    model = "scripted-1"

    def __init__(self, *replies: BaseModel) -> None:
        self.replies = list(replies)
        self.prompts: list[Prompt] = []

    async def structured(self, prompt: Prompt, schema: type[Any]) -> Generated[Any]:
        self.prompts.append(prompt)
        return Generated(self.replies.pop(0), self.model)


def element_number(prompt: Prompt, name: str) -> int:
    table = next(p.text for p in prompt.parts if isinstance(p, Text) and "#1 |" in p.text)
    line = next(row for row in table.splitlines() if f'"{name}"' in row)
    return int(line.split(" |")[0].lstrip("#"))


async def test_review_anchors_notes_to_measured_elements(
    browser: Browser, loopback_guard: AddressGuard, bugfarm: str, tmp_path: Path
) -> None:
    store = LocalArtifactStore(tmp_path)
    views = []
    for viewport in (Viewport.DESKTOP, Viewport.MOBILE):
        async with open_context(browser, viewport, RequestPolicy(loopback_guard)) as context:
            capture = await PageCapturer(store, "run", scroll_pause_ms=50).capture(
                context, f"{bugfarm}/"
            )
        assert capture.probe
        probe = PageProbe.model_validate_json(await store.get(capture.probe))
        views.append(CapturedView(capture, probe, None))

    understanding = PageUnderstanding(
        kind=PageKind.HOME,
        purpose="Help people find a home to buy.",
        audience="House hunters in Baku",
        primary_action="Search listings",
        primary_element=None,
        site_language="en",
    )
    provider = ScriptedProvider(understanding)
    reviewer = PageReviewer(provider, store)

    async def review_with(note_element: int | None) -> Any:
        provider.replies = [
            understanding,
            DesignReview(
                overall="Plain but usable.",
                strengths=["Clear headline"],
                scores=Scores(visual=55, ux=60, content=50, conversion=35, accessibility=40),
                notes=[
                    ReviewNote(
                        element=note_element,
                        viewport="desktop",
                        category="conversion",
                        severity="high",
                        confidence=1.4,
                        title="Search gives no hint of what it searches",
                        description="d",
                        recommendation="r",
                        alternative=None,
                        evidence="desktop section 1",
                    ),
                    ReviewNote(
                        element=None,
                        viewport="all",
                        category="ux",
                        severity="medium",
                        confidence=0.6,
                        title="The page has no clear value proposition",
                        description="d",
                        recommendation="r",
                        alternative=None,
                        evidence="desktop section 1",
                    ),
                ],
            ),
        ]
        return await reviewer.review(views, "en")

    first = await review_with(None)
    review_prompt = provider.prompts[-1]
    images = [p for p in review_prompt.parts if isinstance(p, ImagePart)]
    assert 2 <= len(images) <= 7
    assert all(Image.open(io.BytesIO(i.data)).format == "JPEG" for i in images)
    assert Image.open(io.BytesIO(images[0].data)).width == 1024
    assert first.understanding.kind is PageKind.HOME

    search = element_number(review_prompt, "Search")
    result = await review_with(search)
    anchored, page_level = result.findings
    assert anchored.anchor is not None
    assert anchored.anchor.selector == "#search-btn"
    assert anchored.viewport is Viewport.DESKTOP
    assert anchored.confidence == 1.0
    assert anchored.status is Status.PREDICTED
    assert anchored.source == "agent:ux-designer"
    assert page_level.anchor is None
    assert page_level.viewport is Viewport.DESKTOP
