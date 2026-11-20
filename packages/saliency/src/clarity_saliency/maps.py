import io
from collections.abc import Iterable, Sequence

import numpy as np
from numpy.typing import NDArray
from PIL import Image

Density = NDArray[np.float32]
Box = tuple[float, float, float, float]

_STOPS = np.array(
    [
        (0.00, (37, 52, 148, 0)),
        (0.25, (44, 127, 184, 90)),
        (0.50, (65, 182, 196, 130)),
        (0.70, (254, 217, 118, 170)),
        (0.85, (253, 141, 60, 200)),
        (1.00, (227, 26, 28, 225)),
    ],
    dtype=object,
)


def normalize(values: NDArray[np.floating]) -> Density:
    clipped = np.clip(np.nan_to_num(values.astype(np.float32)), 0, None)
    total = float(clipped.sum())
    if total <= 0:
        return np.full(clipped.shape, 1.0 / clipped.size, dtype=np.float32)
    return clipped / np.float32(total)


def resize_map(density: Density, size: tuple[int, int]) -> Density:
    height, width = size
    image = Image.fromarray(density.astype(np.float32), mode="F")
    resized = np.asarray(image.resize((width, height), Image.Resampling.BILINEAR), dtype=np.float32)
    return normalize(resized)


def blend(weighted: Iterable[tuple[Density, float]]) -> Density:
    items = list(weighted)
    total = sum(weight for _, weight in items)
    if not items or total <= 0:
        raise ValueError("nothing to blend")
    mixed = sum(
        (density * np.float32(weight / total) for density, weight in items), start=np.float32(0)
    )
    return normalize(np.asarray(mixed))


def region_share(density: Density, box: Box) -> float:
    x, y, width, height = box
    rows, cols = density.shape
    top, bottom = max(0, round(y)), min(rows, round(y + height))
    left, right = max(0, round(x)), min(cols, round(x + width))
    if top >= bottom or left >= right:
        return 0.0
    return float(density[top:bottom, left:right].sum())


def stitch(sections: Sequence[tuple[int, Density]], *, height: int, width: int) -> Density:
    page = np.zeros((height, width), dtype=np.float32)
    coverage = np.zeros((height, 1), dtype=np.float32)
    for offset, density in sections:
        rows = min(density.shape[0], height - offset)
        if rows <= 0:
            continue
        page[offset : offset + rows] += density[:rows, :width]
        coverage[offset : offset + rows] += 1
    return (page / np.maximum(coverage, 1)).astype(np.float32)


def to_png(density: Density) -> bytes:
    peak = float(density.max()) or 1.0
    gray = np.round(density / peak * 255).astype(np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(gray, mode="L").save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def colorize(density: Density) -> Image.Image:
    peak = float(density.max()) or 1.0
    level = density / peak
    positions = np.array([stop[0] for stop in _STOPS], dtype=np.float32)
    colors = np.array([stop[1] for stop in _STOPS], dtype=np.float32)
    channels = [np.interp(level, positions, colors[:, index]) for index in range(4)]
    rgba = np.stack(channels, axis=-1).round().astype(np.uint8)
    return Image.fromarray(rgba, mode="RGBA")
