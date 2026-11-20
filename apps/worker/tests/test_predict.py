import io
import os
from pathlib import Path

import pytest
from PIL import Image
from playwright.async_api import Browser

from clarity_core.domain.viewport import Viewport
from clarity_core.net.guard import AddressGuard
from clarity_saliency.predictor import AttentionPredictor
from clarity_worker.browser import open_context
from clarity_worker.capture import PageCapturer
from clarity_worker.policy import RequestPolicy
from clarity_worker.predict import PagePredictor
from clarity_worker.store import LocalArtifactStore

MODEL_DIR = Path(
    os.environ.get("CLARITY_MODEL_DIR", Path(__file__).resolve().parents[3] / "models")
)


@pytest.fixture(scope="module")
def attention() -> AttentionPredictor:
    if not any(MODEL_DIR.glob("*.onnx")):
        pytest.skip("saliency models are not available")
    return AttentionPredictor(MODEL_DIR)


@pytest.mark.parametrize("viewport", [Viewport.DESKTOP, Viewport.MOBILE])
async def test_predicts_attention_and_clicks_for_a_captured_page(
    browser: Browser,
    loopback_guard: AddressGuard,
    bugfarm: str,
    tmp_path: Path,
    attention: AttentionPredictor,
    viewport: Viewport,
) -> None:
    store = LocalArtifactStore(tmp_path)
    async with open_context(browser, viewport, RequestPolicy(loopback_guard)) as context:
        capture = await PageCapturer(store, "run", scroll_pause_ms=50).capture(
            context, f"{bugfarm}/"
        )

    prediction = await PagePredictor(store, attention).predict(capture)

    assert len(prediction.sections) == len(capture.sections)
    assert 0 < prediction.agreement <= 1
    heatmap = Image.open(io.BytesIO(await store.get(prediction.heatmap)))
    assert heatmap.width == 360
    assert abs(heatmap.height - capture.page_height * prediction.heatmap_scale) <= 1
    section_map = Image.open(io.BytesIO(await store.get(prediction.sections[0].combined)))
    assert section_map.size == (viewport.width, viewport.height)

    clicks = [element.click for element in prediction.elements if element.click is not None]
    assert sum(clicks) == pytest.approx(1)
    search = next(e for e in prediction.elements if e.name == "Search")
    assert search.section == 0
    assert search.attention > 0
    headline = next(e for e in prediction.elements if e.tag == "h1")
    assert headline.click is None
    assert prediction.top_clicks(3)
