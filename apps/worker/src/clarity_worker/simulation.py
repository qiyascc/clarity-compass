import asyncio
import contextlib
import io
import re
from dataclasses import dataclass
from typing import Any

import numpy as np
from PIL import Image
from playwright.async_api import Browser, Page
from playwright.async_api import Error as PlaywrightError

from clarity_ai.agents import SimulationAgent
from clarity_ai.schemas import DesignPatch
from clarity_core.domain.findings import Box, Finding
from clarity_core.domain.probe import ProbedElement
from clarity_core.domain.viewport import Viewport
from clarity_core.net.guard import AddressGuard
from clarity_persistence.secrets import SiteLogin
from clarity_saliency.maps import region_share, resize_map, to_png
from clarity_saliency.predictor import AttentionPredictor
from clarity_worker.browser import open_context
from clarity_worker.login import sign_in
from clarity_worker.policy import RequestPolicy
from clarity_worker.probe import run_probe
from clarity_worker.store import ArtifactStore

UNSAFE_CSS = re.compile(
    r"(@import|url\s*\(|expression\s*\(|javascript:|behavior\s*:|-moz-binding)", re.I
)
MAX_CSS = 6_000
MARK = "data-clarity-target"

MARK_TARGET = """([selector, xpath, text, mark]) => {
  const bySelector = () => {
    try {
      return selector && document.querySelector(selector);
    } catch {
      return null;
    }
  };
  const first = XPathResult.FIRST_ORDERED_NODE_TYPE;
  const byXpath = () => xpath
    ? document.evaluate(xpath, document, null, first, null).singleNodeValue
    : null;
  const byText = () => text
    ? [...document.querySelectorAll('a, button, [role], h1, h2, h3, p, span, label')]
        .find((el) => el.textContent.replace(/\\s+/g, ' ').trim() === text.trim())
    : null;
  const element = bySelector() || byXpath() || byText();
  if (!element) return false;
  element.setAttribute(mark, '');
  return true;
}"""

CENTER = """(mark) => {
  const element = document.querySelector(`[${mark}]`);
  element.scrollIntoView({ block: 'center', inline: 'nearest' });
  const rect = element.getBoundingClientRect();
  return {
    x: rect.left, y: rect.top, width: rect.width, height: rect.height, scrollY: window.scrollY,
  };
}"""

APPLY = """([css, changes]) => {
  const style = document.createElement('style');
  style.setAttribute('data-clarity-patch', '');
  style.textContent = css;
  document.head.append(style);
  for (const change of changes) {
    const element = document.querySelector(change.selector);
    if (!element) continue;
    if (change.text !== null) {
      const node = [...element.childNodes].find((n) => n.nodeType === 3 && n.textContent.trim());
      if (node) node.textContent = change.text;
      else if (!element.children.length) element.textContent = change.text;
    }
    if (change.move !== 'none' && change.reference) {
      const reference = document.querySelector(change.reference);
      if (reference && !element.contains(reference)) {
        const where = change.move === 'before' ? 'beforebegin' : 'afterend';
        reference.insertAdjacentElement(where, element);
      }
    }
  }
}"""


class SimulationError(Exception):
    pass


ANIMATIONS_DONE = """() => document.getAnimations().every((animation) => {
  const timing = animation.effect?.getComputedTiming();
  return animation.playState !== 'running' || !timing || timing.iterations === Infinity;
})"""


async def settle(page: Page) -> None:
    """Waits for the network and for intro animations, such as loaders, to finish."""
    with contextlib.suppress(PlaywrightError):
        await page.wait_for_load_state("networkidle", timeout=4_000)
    with contextlib.suppress(PlaywrightError):
        await page.wait_for_function(ANIMATIONS_DONE, timeout=8_000, polling=250)
    await page.wait_for_timeout(300)


@dataclass(frozen=True)
class Frame:
    screenshot: bytes
    heat: bytes
    box: Box
    share: float
    rank: int
    candidates: int

    def summary(self, screenshot: str, heat: str) -> dict[str, Any]:
        return {
            "screenshot": screenshot,
            "heat": heat,
            "box": self.box.model_dump(),
            "attention": round(self.share, 5),
            "rank": self.rank,
            "elements": self.candidates,
        }


class FixSimulator:
    def __init__(
        self,
        browser: Browser,
        store: ArtifactStore,
        guard: AddressGuard,
        attention: AttentionPredictor,
        agent: SimulationAgent,
    ) -> None:
        self.browser = browser
        self.store = store
        self.guard = guard
        self.attention = attention
        self.agent = agent

    async def simulate(
        self,
        finding: Finding,
        language: str,
        prefix: str,
        login: SiteLogin | None = None,
    ) -> tuple[DesignPatch, dict[str, Any]]:
        if finding.anchor is None:
            raise SimulationError("the finding is not tied to an element")
        viewport = finding.viewport
        async with open_context(self.browser, viewport, RequestPolicy(self.guard)) as context:
            if login:
                await sign_in(context, login)
            page = await context.new_page()
            await page.goto(finding.page_url, wait_until="load", timeout=30_000)
            await settle(page)
            anchor = finding.anchor
            found = await page.evaluate(
                MARK_TARGET, [anchor.selector, anchor.xpath, anchor.text, MARK]
            )
            if not found:
                raise SimulationError("the element is no longer on the live page")

            before, elements, target = await self._frame(page, viewport)
            lines = [
                f"#{number} | {element.selector} | {element.role or element.tag} | "
                f'"{(element.name or element.text)[:60]}" | box {element.box.x:.0f},'
                f"{element.box.y:.0f} {element.box.width:.0f}x{element.box.height:.0f} | "
                f"font {element.font_size:g}px {element.font_weight} | color {element.color} "
                f"on {element.background}"
                for number, element in enumerate(elements, start=1)
            ]
            description = (
                f"{finding.title}\n{finding.description}\nRecommendation: {finding.recommendation}"
            )
            generated = await self.agent.run(
                description, _jpeg(before.screenshot), lines, target, language
            )
            patch = generated.value
            await page.evaluate(APPLY, [_safe_css(patch.css), _changes(patch, elements)])
            await page.wait_for_timeout(400)
            after, _, _ = await self._frame(page, viewport)

        keys = {
            name: await self.store.put(f"{prefix}/{name}.png", data)
            for name, data in (
                ("before", before.screenshot),
                ("before-heat", before.heat),
                ("after", after.screenshot),
                ("after-heat", after.heat),
            )
        }
        result = {
            "explanation": patch.explanation,
            "viewport": viewport.value,
            "before": before.summary(keys["before"], keys["before-heat"]),
            "after": after.summary(keys["after"], keys["after-heat"]),
            "change": round(after.share - before.share, 5),
        }
        return patch, result

    async def _frame(
        self, page: Page, viewport: Viewport
    ) -> tuple[Frame, list[ProbedElement], int]:
        target = await page.evaluate(CENTER, MARK)
        await page.wait_for_timeout(250)
        shot = await page.screenshot(animations="disabled")
        probe = await run_probe(page)
        scroll = target["scrollY"]
        box = Box(x=target["x"], y=target["y"], width=target["width"], height=target["height"])
        visible = [
            element
            for element in probe.elements
            if element.visible
            and (element.interactive or element.tag in {"h1", "h2", "h3"} or element.text)
            and scroll <= element.box.y < scroll + viewport.height
        ][:80]

        image = np.asarray(Image.open(io.BytesIO(shot)).convert("RGB"))
        attention = await asyncio.to_thread(self.attention.predict, image)
        density = resize_map(attention.combined, (viewport.height, viewport.width))

        def share(candidate: Box) -> float:
            return region_share(
                density, (candidate.x, candidate.y, candidate.width, candidate.height)
            )

        target_share = share(box)
        shares = [share(e.box.model_copy(update={"y": e.box.y - scroll})) for e in visible]
        rank = 1 + sum(1 for value in shares if value > target_share)
        number = 1 + min(
            range(len(visible)),
            key=lambda i: abs(visible[i].box.y - scroll - box.y) + abs(visible[i].box.x - box.x),
            default=0,
        )
        frame = Frame(shot, to_png(density), box, target_share, rank, len(visible))
        return frame, visible, number


def _safe_css(css: str) -> str:
    if UNSAFE_CSS.search(css):
        raise SimulationError("the proposed CSS loads external resources")
    return css[:MAX_CSS]


def _changes(patch: DesignPatch, elements: list[ProbedElement]) -> list[dict[str, Any]]:
    def selector(number: int | None) -> str | None:
        if number is None or not 1 <= number <= len(elements):
            return None
        return elements[number - 1].selector

    return [
        {
            "selector": selector(change.element),
            "text": change.text,
            "move": change.move,
            "reference": selector(change.reference),
        }
        for change in patch.changes
        if selector(change.element)
    ]


def _jpeg(raw: bytes) -> bytes:
    buffer = io.BytesIO()
    Image.open(io.BytesIO(raw)).convert("RGB").save(buffer, format="JPEG", quality=75)
    return buffer.getvalue()
