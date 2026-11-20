from pathlib import Path
from typing import Protocol

import numpy as np
import onnxruntime  # type: ignore[import-untyped]
from numpy.typing import NDArray
from PIL import Image

from clarity_saliency.maps import Density, normalize, resize_map

Rgb = NDArray[np.uint8]

IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


class SaliencyModel(Protocol):
    name: str

    def predict(self, image: Rgb) -> Density: ...


def _resize(image: Rgb, size: tuple[int, int], method: Image.Resampling) -> Image.Image:
    height, width = size
    return Image.fromarray(image).convert("RGB").resize((width, height), method)


def _session(path: Path) -> onnxruntime.InferenceSession:
    options = onnxruntime.SessionOptions()
    options.log_severity_level = 3
    return onnxruntime.InferenceSession(str(path), options, providers=_providers())


def _providers() -> list[str]:
    available = onnxruntime.get_available_providers()
    preferred = ["CUDAExecutionProvider", "CoreMLExecutionProvider", "CPUExecutionProvider"]
    return [provider for provider in preferred if provider in available]


class Foveacast:
    """MSI-Net fine-tuned on UEyes. Fixed 240x320 input, RGB in [0, 255]."""

    INPUT_SIZE = (240, 320)

    def __init__(self, path: Path, window: str) -> None:
        self.name = f"foveacast-{window}"
        self.window = window
        self._session = _session(path)
        self._input = self._session.get_inputs()[0].name

    def predict(self, image: Rgb) -> Density:
        height, width = self.INPUT_SIZE
        resized = (
            Image.fromarray(image).convert("RGB").resize((width, height), Image.Resampling.BILINEAR)
        )
        tensor = np.asarray(resized, dtype=np.float32).transpose(2, 0, 1)[None]
        (output,) = self._session.run(None, {self._input: tensor})
        return resize_map(normalize(np.asarray(output)[0, 0]), image.shape[:2])


class MediaAttention:
    """UNISAL fine-tuned on UEyes, one ONNX graph per input aspect ratio."""

    def __init__(self, paths: list[Path]) -> None:
        if not paths:
            raise ValueError("MediaAttention needs at least one exported graph")
        self.name = "mediaattention-ads"
        self._graphs: list[tuple[tuple[int, int], onnxruntime.InferenceSession]] = []
        for path in paths:
            session = _session(path)
            _, _, height, width = session.get_inputs()[0].shape
            self._graphs.append(((int(height), int(width)), session))

    def predict(self, image: Rgb) -> Density:
        (height, width), session = self._closest(image.shape[0] / image.shape[1])
        resized = (
            Image.fromarray(image).convert("RGB").resize((width, height), Image.Resampling.LANCZOS)
        )
        pixels = (np.asarray(resized, dtype=np.float32) / 255 - IMAGENET_MEAN) / IMAGENET_STD
        tensor = pixels.transpose(2, 0, 1)[None].astype(np.float32)
        (log_density,) = session.run(None, {"image": tensor})
        density = np.exp(np.asarray(log_density, dtype=np.float32)[0, 0])
        return resize_map(normalize(density), image.shape[:2])

    def _closest(self, ratio: float) -> tuple[tuple[int, int], onnxruntime.InferenceSession]:
        return min(self._graphs, key=lambda graph: abs(np.log(graph[0][0] / graph[0][1] / ratio)))
