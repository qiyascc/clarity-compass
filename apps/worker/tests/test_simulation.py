import io
from pathlib import Path
from typing import Any

import pytest
from PIL import Image
from playwright.async_api import Browser

from clarity_ai.agents import SimulationAgent
from clarity_ai.provider import Generated, Prompt
from clarity_ai.schemas import DesignPatch
from clarity_core.domain.findings import Category, ElementAnchor, Finding, Severity, Status
from clarity_core.domain.viewport import Viewport
from clarity_core.net.guard import AddressGuard
from clarity_saliency.predictor import AttentionPredictor
from clarity_worker.simulation import FixSimulator, SimulationError
from clarity_worker.store import LocalArtifactStore

MODEL_DIR = Path(__file__).resolve().parents[3] / "models"


class PatchProvider:
    name = "scripted"
    model = "scripted-1"

    def __init__(self, css: str) -> None:
        self.css = css
        self.prompts: list[Prompt] = []

    async def structured(self, prompt: Prompt, schema: type[Any]) -> Generated[Any]:
        self.prompts.append(prompt)
        return Generated(
            DesignPatch(css=self.css, changes=[], explanation="Bigger CTA."), self.model
        )


@pytest.fixture(scope="module")
def attention() -> AttentionPredictor:
    if not any(MODEL_DIR.glob("*.onnx")):
        pytest.skip("saliency models are not available")
    return AttentionPredictor(MODEL_DIR)


def finding(url: str) -> Finding:
    return Finding(
        page_url=url,
        viewport=Viewport.DESKTOP,
        category=Category.CONVERSION,
        severity=Severity.HIGH,
        status=Status.PREDICTED,
        confidence=0.7,
        title="Contact button is easy to miss",
        description="d",
        recommendation="Make the contact button larger and more prominent.",
        anchor=ElementAnchor(selector="section:nth-of-type(3) > a.btn", text="Contact agent"),
    )


async def test_a_more_prominent_button_draws_more_attention(
    browser: Browser,
    loopback_guard: AddressGuard,
    bugfarm: str,
    tmp_path: Path,
    attention: AttentionPredictor,
) -> None:
    store = LocalArtifactStore(tmp_path)
    provider = PatchProvider(
        "a.btn { padding: 28px 64px; font-size: 28px; font-weight: 700; background: #e4002b; }"
    )
    simulator = FixSimulator(browser, store, loopback_guard, attention, SimulationAgent(provider))
    patch, result = await simulator.simulate(finding(f"{bugfarm}/listings/1.html"), "en", "sim/1")

    assert patch.explanation == "Bigger CTA."
    assert result["after"]["box"]["width"] > result["before"]["box"]["width"]
    assert result["after"]["attention"] > result["before"]["attention"]
    assert result["change"] > 0
    before = Image.open(io.BytesIO(await store.get(result["before"]["screenshot"])))
    assert before.size == (Viewport.DESKTOP.width, Viewport.DESKTOP.height)
    assert "element #" in str(provider.prompts[0].parts)


async def test_external_resources_in_css_are_refused(
    browser: Browser,
    loopback_guard: AddressGuard,
    bugfarm: str,
    tmp_path: Path,
    attention: AttentionPredictor,
) -> None:
    provider = PatchProvider("a.btn { background: url(https://evil.test/x.png); }")
    simulator = FixSimulator(
        browser, LocalArtifactStore(tmp_path), loopback_guard, attention, SimulationAgent(provider)
    )
    with pytest.raises(SimulationError, match="external"):
        await simulator.simulate(finding(f"{bugfarm}/listings/1.html"), "en", "sim/2")


async def test_missing_elements_are_reported(
    browser: Browser,
    loopback_guard: AddressGuard,
    bugfarm: str,
    tmp_path: Path,
    attention: AttentionPredictor,
) -> None:
    gone = finding(f"{bugfarm}/about.html").model_copy(
        update={"anchor": ElementAnchor(selector="#nope", text="Nothing like this")}
    )
    simulator = FixSimulator(
        browser,
        LocalArtifactStore(tmp_path),
        loopback_guard,
        attention,
        SimulationAgent(PatchProvider("")),
    )
    with pytest.raises(SimulationError, match="no longer"):
        await simulator.simulate(gone, "en", "sim/3")
