import io

import numpy as np
import pytest
from PIL import Image

from clarity_saliency.maps import (
    blend,
    colorize,
    normalize,
    region_share,
    resize_map,
    stitch,
    to_png,
)


def test_normalize_sums_to_one_and_survives_zeros() -> None:
    assert normalize(np.array([[1.0, 3.0]])).sum() == pytest.approx(1.0)
    flat = normalize(np.zeros((2, 2)))
    assert flat.sum() == pytest.approx(1.0)
    assert np.allclose(flat, 0.25)


def test_normalize_rejects_negative_mass() -> None:
    assert normalize(np.array([[-1.0, 1.0]])).min() >= 0


def test_resize_keeps_distribution() -> None:
    density = normalize(np.random.default_rng(1).random((24, 32)))
    resized = resize_map(density, (90, 120))
    assert resized.shape == (90, 120)
    assert resized.sum() == pytest.approx(1.0)


def test_blend_weights_maps() -> None:
    left = normalize(np.array([[1.0, 0.0]]))
    right = normalize(np.array([[0.0, 1.0]]))
    mixed = blend([(left, 3.0), (right, 1.0)])
    assert mixed[0, 0] == pytest.approx(0.75)


def test_region_share() -> None:
    density = normalize(np.ones((100, 100)))
    assert region_share(density, (0, 0, 50, 100)) == pytest.approx(0.5)
    assert region_share(density, (-20, -20, 40, 40)) == pytest.approx(0.04)
    assert region_share(density, (500, 500, 10, 10)) == 0


def test_stitch_places_sections_by_scroll_offset() -> None:
    top = np.full((10, 4), 1 / 40, dtype=np.float32)
    bottom = np.full((10, 4), 1 / 40, dtype=np.float32) * 2
    page = stitch([(0, top), (6, bottom)], height=16, width=4)
    assert page.shape == (16, 4)
    assert page[0, 0] == pytest.approx(top[0, 0])
    assert page[15, 0] == pytest.approx(bottom[0, 0])
    assert page[8, 0] == pytest.approx((top[0, 0] + bottom[0, 0]) / 2)


def test_png_roundtrip_and_colorize() -> None:
    density = normalize(np.random.default_rng(2).random((20, 30)))
    gray = Image.open(io.BytesIO(to_png(density)))
    assert gray.mode == "L"
    assert gray.size == (30, 20)
    assert np.asarray(gray).max() == 255
    overlay = colorize(density)
    assert overlay.mode == "RGBA"
    assert overlay.size == (30, 20)
