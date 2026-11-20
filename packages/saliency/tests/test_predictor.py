from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray

from clarity_saliency.maps import normalize
from clarity_saliency.predictor import AttentionPredictor, correlation


def test_correlation_bounds() -> None:
    rng = np.random.default_rng(3)
    density = normalize(rng.random((10, 10)))
    assert correlation(density, density) == pytest.approx(1.0)
    assert correlation(density, normalize(density.max() - density)) == pytest.approx(-1.0)
    assert correlation(density, normalize(np.ones((10, 10)))) == 0.0


def test_predictor_combines_models(model_dir: Path, landing_page: NDArray[np.uint8]) -> None:
    attention = AttentionPredictor(model_dir).predict(landing_page)
    assert set(attention.windows) == {"1s", "3s", "7s"}
    assert attention.combined.shape == landing_page.shape[:2]
    assert attention.combined.sum() == pytest.approx(1.0, abs=1e-4)
    assert 0.3 < attention.agreement <= 1.0
