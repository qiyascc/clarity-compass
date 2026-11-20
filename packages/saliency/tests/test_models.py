from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray

from clarity_saliency.maps import region_share
from clarity_saliency.models import Foveacast, MediaAttention, SaliencyModel


@pytest.mark.parametrize("window", ["1s", "3s", "7s"])
def test_foveacast_returns_a_density_at_image_size(
    model_dir: Path, landing_page: NDArray[np.uint8], window: str
) -> None:
    model = Foveacast(model_dir / f"foveacast-v3-{window}-int8.onnx", window)
    density = model.predict(landing_page)
    assert density.shape == landing_page.shape[:2]
    assert density.sum() == pytest.approx(1.0, abs=1e-4)


def test_mediaattention_picks_the_graph_for_the_aspect_ratio(
    model_dir: Path, landing_page: NDArray[np.uint8]
) -> None:
    model = MediaAttention(sorted(model_dir.glob("mediaattention-ads-*.onnx")))
    density = model.predict(landing_page)
    assert density.shape == landing_page.shape[:2]
    portrait = model.predict(np.ascontiguousarray(landing_page[:, :400]))
    assert portrait.shape == (900, 400)


def test_salient_blocks_draw_more_attention_than_empty_space(
    model_dir: Path, landing_page: NDArray[np.uint8]
) -> None:
    models: list[SaliencyModel] = [
        Foveacast(model_dir / "foveacast-v3-3s-int8.onnx", "3s"),
        MediaAttention(sorted(model_dir.glob("mediaattention-ads-*.onnx"))),
    ]
    for model in models:
        density = model.predict(landing_page)
        headline = region_share(density, (520, 300, 400, 120))
        empty_corner = region_share(density, (0, 700, 400, 120))
        assert headline > empty_corner * 3, model.name
