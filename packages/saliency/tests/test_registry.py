import hashlib
from pathlib import Path

import pytest

from clarity_saliency.registry import MODEL_FILES, ChecksumError, ModelFile, fetch


def local_model(tmp_path: Path, content: bytes, sha256: str | None = None) -> ModelFile:
    source = tmp_path / "source.onnx"
    source.write_bytes(content)
    return ModelFile("model.onnx", source.as_uri(), sha256 or hashlib.sha256(content).hexdigest())


def test_fetch_downloads_and_verifies(tmp_path: Path) -> None:
    model = local_model(tmp_path, b"weights")
    (path,) = fetch(tmp_path / "models", (model,))
    assert path.read_bytes() == b"weights"


def test_existing_valid_files_are_kept(tmp_path: Path) -> None:
    model = local_model(tmp_path, b"weights")
    target = tmp_path / "models" / "model.onnx"
    target.parent.mkdir()
    target.write_bytes(b"weights")
    (tmp_path / "source.onnx").unlink()
    assert fetch(tmp_path / "models", (model,)) == [target]


def test_checksum_mismatch_is_rejected(tmp_path: Path) -> None:
    model = local_model(tmp_path, b"tampered", sha256="0" * 64)
    with pytest.raises(ChecksumError):
        fetch(tmp_path / "models", (model,))
    assert not list((tmp_path / "models").iterdir())


def test_registry_is_pinned() -> None:
    assert all(len(model.sha256) == 64 for model in MODEL_FILES)
    assert all(model.url.startswith("https://") for model in MODEL_FILES)
