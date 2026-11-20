from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import numpy as np

from clarity_saliency.maps import Density, blend
from clarity_saliency.models import Foveacast, MediaAttention, Rgb

WINDOWS = ("1s", "3s", "7s")


@dataclass(frozen=True)
class Attention:
    windows: dict[str, Density]
    combined: Density
    agreement: float


class AttentionPredictor:
    """Foveacast gives the time windows; the combined map blends it with MediaAttention.

    `agreement` is the Pearson correlation between the two models on the same
    image. Low agreement means the prediction deserves less trust.
    """

    def __init__(self, model_dir: Path, *, mediaattention_weight: float = 0.4) -> None:
        self.model_dir = model_dir
        self.mediaattention_weight = mediaattention_weight

    @cached_property
    def foveacast(self) -> dict[str, Foveacast]:
        return {
            window: Foveacast(self.model_dir / f"foveacast-v3-{window}-int8.onnx", window)
            for window in WINDOWS
        }

    @cached_property
    def mediaattention(self) -> MediaAttention:
        return MediaAttention(sorted(self.model_dir.glob("mediaattention-ads-*.onnx")))

    def predict(self, image: Rgb) -> Attention:
        windows = {window: model.predict(image) for window, model in self.foveacast.items()}
        secondary = self.mediaattention.predict(image)
        combined = blend(
            [
                (windows["3s"], 1 - self.mediaattention_weight),
                (secondary, self.mediaattention_weight),
            ]
        )
        return Attention(windows, combined, correlation(windows["3s"], secondary))


def correlation(left: Density, right: Density) -> float:
    a = left.ravel().astype(np.float64)
    b = right.ravel().astype(np.float64)
    a -= a.mean()
    b -= b.mean()
    denominator = float(np.sqrt((a * a).sum() * (b * b).sum()))
    return float((a * b).sum() / denominator) if denominator else 0.0
