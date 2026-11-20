import os
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray
from PIL import Image, ImageDraw

MODEL_DIR = Path(
    os.environ.get("CLARITY_MODEL_DIR", Path(__file__).resolve().parents[3] / "models")
)


@pytest.fixture(scope="session")
def model_dir() -> Path:
    if not any(MODEL_DIR.glob("*.onnx")):
        pytest.skip(f"no ONNX models in {MODEL_DIR}; run python -m clarity_saliency fetch")
    return MODEL_DIR


@pytest.fixture(scope="session")
def landing_page() -> NDArray[np.uint8]:
    image = Image.new("RGB", (1440, 900), "#f4f4f4")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1440, 64), fill="#ffffff")
    draw.rectangle((520, 300, 920, 420), fill="#111111")
    draw.rectangle((620, 480, 820, 540), fill="#e4002b")
    return np.asarray(image)
