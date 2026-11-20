import asyncio
import io

import numpy as np
from PIL import Image

from clarity_core.domain.capture import PageCapture, Section
from clarity_core.domain.findings import Box
from clarity_core.domain.prediction import ElementPrediction, PagePrediction, SectionAttention
from clarity_core.domain.probe import PageProbe, ProbedElement
from clarity_core.domain.viewport import Viewport
from clarity_saliency.maps import Density, region_share, resize_map, stitch, to_png
from clarity_saliency.predictor import AttentionPredictor
from clarity_worker.clicks import ClickModel
from clarity_worker.store import ArtifactStore

HEATMAP_WIDTH = 360
MAX_ELEMENTS = 400
HEADINGS = {"h1", "h2", "h3"}


class PagePredictor:
    def __init__(
        self,
        store: ArtifactStore,
        attention: AttentionPredictor,
        clicks: ClickModel | None = None,
    ) -> None:
        self.store = store
        self.attention = attention
        self.clicks = clicks or ClickModel()

    async def predict(self, capture: PageCapture) -> PagePrediction:
        if capture.probe is None:
            raise ValueError("capture has no probe")
        probe = PageProbe.model_validate_json(await self.store.get(capture.probe))
        viewport = capture.viewport
        size = (viewport.height, viewport.width)

        sections: list[SectionAttention] = []
        densities: list[Density] = []
        for section in capture.sections:
            stored, density = await self._section(section, size)
            sections.append(stored)
            densities.append(density)

        page = stitch(
            [(s.scroll_y, d) for s, d in zip(capture.sections, densities, strict=True)],
            height=capture.page_height,
            width=viewport.width,
        )
        scale = HEATMAP_WIDTH / viewport.width
        compact = resize_map(page, (max(1, round(capture.page_height * scale)), HEATMAP_WIDTH))
        heatmap = await self.store.put(_sibling(capture, "attention.png"), to_png(compact))

        candidates = _candidates(probe)
        elements = [_element(item, capture.sections, densities, viewport) for item in candidates]
        scored = self.clicks.score(
            candidates, elements, viewport_area=viewport.width * viewport.height
        )
        return PagePrediction(
            sections=sections,
            heatmap=heatmap,
            heatmap_scale=scale,
            agreement=float(np.mean([s.agreement for s in sections])) if sections else 0.0,
            elements=scored,
            models=["foveacast-v3-int8", "mediaattention-ads-v1"],
        )

    async def _section(
        self, section: Section, size: tuple[int, int]
    ) -> tuple[SectionAttention, Density]:
        raw = await self.store.get(section.screenshot)
        image = np.asarray(Image.open(io.BytesIO(raw)).convert("RGB"))
        attention = await asyncio.to_thread(self.attention.predict, image)

        base = section.screenshot.removesuffix(".png")
        combined = resize_map(attention.combined, size)
        windows = {
            name: await self.store.put(f"{base}.attention-{name}.png", to_png(resize_map(d, size)))
            for name, d in attention.windows.items()
        }
        stored = SectionAttention(
            index=section.index,
            scroll_y=section.scroll_y,
            height=section.height,
            combined=await self.store.put(f"{base}.attention.png", to_png(combined)),
            windows=windows,
            agreement=round(attention.agreement, 4),
        )
        return stored, combined


def _candidates(probe: PageProbe) -> list[ProbedElement]:
    chosen = [
        element
        for element in probe.elements
        if element.visible
        and element.box.width * element.box.height > 0
        and (element.interactive or element.tag in HEADINGS)
    ]
    return chosen[:MAX_ELEMENTS]


def _element(
    element: ProbedElement,
    sections: list[Section],
    densities: list[Density],
    viewport: Viewport,
) -> ElementPrediction:
    index, local = _locate(element, sections, viewport)
    share = region_share(densities[index], (local.x, local.y, local.width, local.height))
    area_share = max(local.width * local.height / (viewport.width * viewport.height), 1e-6)
    return ElementPrediction(
        index=element.index,
        selector=element.selector,
        tag=element.tag,
        name=element.name or element.text,
        box=element.box,
        interactive=element.interactive,
        section=sections[index].index,
        attention=round(min(share, 1.0), 6),
        attention_density=round(share / area_share, 4),
    )


def _locate(element: ProbedElement, sections: list[Section], viewport: Viewport) -> tuple[int, Box]:
    box = element.box
    if element.position == "fixed":
        return 0, box

    def visible_rows(section: Section) -> float:
        top = max(box.y, section.scroll_y)
        bottom = min(box.y + box.height, section.scroll_y + viewport.height)
        return max(0.0, bottom - top)

    index = max(range(len(sections)), key=lambda i: (visible_rows(sections[i]), -i))
    local = box.model_copy(update={"y": box.y - sections[index].scroll_y})
    return index, local


def _sibling(capture: PageCapture, name: str) -> str:
    folder = capture.sections[0].screenshot.rsplit("/", 1)[0] if capture.sections else "unknown"
    return f"{folder}/{name}"
