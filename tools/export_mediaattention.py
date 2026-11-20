# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "huggingface_hub>=0.26",
#   "mediaattention[unisal]==0.2.1",
#   "numpy",
#   "onnx>=1.17",
#   "onnxruntime>=1.20",
#   "onnxscript>=0.1",
#   "torch>=2.5",
# ]
#
# [[tool.uv.index]]
# name = "pytorch-cpu"
# url = "https://download.pytorch.org/whl/cpu"
# explicit = true
#
# [tool.uv.sources]
# torch = { index = "pytorch-cpu" }
# ///
"""Export MediaAttention-Ads (UNISAL fine-tuned on UEyes) to ONNX.

UNISAL picks its input size from the image aspect ratio, so one graph is
exported per viewport shape. The graph returns log fixation density at the
input resolution; callers resize and exponentiate.

    uv run tools/export_mediaattention.py models/
"""

import sys
from pathlib import Path

import numpy as np
import onnxruntime
import torch
from mediaattention.saliency import _unisal, _unisal_size

TOLERANCE = 1e-3

VIEWPORTS = {"desktop": (900, 1440), "tablet": (1112, 834), "mobile": (844, 390)}


class StaticUnisal(torch.nn.Module):
    def __init__(self, model: torch.nn.Module, size: tuple[int, int]) -> None:
        super().__init__()
        self.model = model
        self.size = size

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        log_density = self.model(
            image[:, None], target_size=self.size, source="SALICON", static=True
        )
        return log_density[:, 0]


def main(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    model = _unisal("cpu", "ads")
    for name, (height, width) in VIEWPORTS.items():
        size = _unisal_size(height, width)
        wrapper = StaticUnisal(model, size).eval()
        target = out_dir / f"mediaattention-ads-{size[0]}x{size[1]}.onnx"
        with torch.no_grad():
            torch.onnx.export(
                wrapper,
                (torch.zeros(1, 3, *size),),
                target,
                input_names=["image"],
                output_names=["log_density"],
                opset_version=17,
                dynamo=False,
            )
        error = parity(wrapper, target, size)
        if error > TOLERANCE:
            raise SystemExit(f"{target}: ONNX differs from PyTorch by {error:.2e}")
        print(f"{name}: {target} ({size[0]}x{size[1]}, max abs err {error:.1e})")


def parity(model: torch.nn.Module, path: Path, size: tuple[int, int]) -> float:
    generator = torch.Generator().manual_seed(7)
    sample = torch.randn(1, 3, *size, generator=generator)
    with torch.no_grad():
        expected = model(sample).numpy()
    session = onnxruntime.InferenceSession(path, providers=["CPUExecutionProvider"])
    (actual,) = session.run(None, {"image": sample.numpy()})
    return float(np.abs(np.exp(actual) - np.exp(expected)).max() / np.exp(expected).max())


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "models"))
