from pathlib import Path

import pytest

from clarity_worker.store import LocalArtifactStore


async def test_roundtrip(tmp_path: Path) -> None:
    store = LocalArtifactStore(tmp_path)
    key = await store.put("runs/1/shot.png", b"png")
    assert await store.get(key) == b"png"


async def test_rejects_keys_outside_root(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="escapes"):
        await LocalArtifactStore(tmp_path / "store").put("../evil", b"x")
