import hashlib
import urllib.request
from dataclasses import dataclass
from pathlib import Path

FOVEACAST = "https://github.com/khawkins98/foveacast-training/releases/download/v0.2.0"
CLARITY = "https://github.com/qiyascc/clarity-compass/releases/download/models-v1"


@dataclass(frozen=True)
class ModelFile:
    name: str
    url: str
    sha256: str


MODEL_FILES = (
    ModelFile(
        "foveacast-v3-1s-int8.onnx",
        f"{FOVEACAST}/foveacast-v3-1s-int8.onnx",
        "3d94ce75c9500b61924193a03a098fa1fa704f39fbbf2ea7083ecc00796fab2b",
    ),
    ModelFile(
        "foveacast-v3-3s-int8.onnx",
        f"{FOVEACAST}/foveacast-v3-3s-int8.onnx",
        "e02e3071af18e11dbfab8b633dfc601d53662d0d2884d827ab03a8e363707d68",
    ),
    ModelFile(
        "foveacast-v3-7s-int8.onnx",
        f"{FOVEACAST}/foveacast-v3-7s-int8.onnx",
        "5ebbe008d7a693cc6b55341bad47c008e1102b7bf46693cfe084849ccb8242bb",
    ),
    ModelFile(
        "mediaattention-ads-256x416.onnx",
        f"{CLARITY}/mediaattention-ads-256x416.onnx",
        "5eafbaca018c21c3db30adabf896f44986f8f8393dee105a7069d2fbeedcac68",
    ),
    ModelFile(
        "mediaattention-ads-384x288.onnx",
        f"{CLARITY}/mediaattention-ads-384x288.onnx",
        "97097ee259a34c2dbb9bf41082fb8e4d41251eb78bdf6debaf3512a3277b95ae",
    ),
    ModelFile(
        "mediaattention-ads-416x256.onnx",
        f"{CLARITY}/mediaattention-ads-416x256.onnx",
        "21adebefcf4da35810d75ce11252a5ef5fcddd49264b95ddb7cf9e6aef86670b",
    ),
)


class ChecksumError(RuntimeError):
    pass


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            sha.update(chunk)
    return sha.hexdigest()


def fetch(directory: Path, files: tuple[ModelFile, ...] = MODEL_FILES) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    fetched = []
    for model in files:
        target = directory / model.name
        if target.is_file() and digest(target) == model.sha256:
            fetched.append(target)
            continue
        partial = target.with_suffix(".part")
        urllib.request.urlretrieve(model.url, partial)
        if digest(partial) != model.sha256:
            partial.unlink()
            raise ChecksumError(f"{model.name} does not match its published checksum")
        partial.replace(target)
        fetched.append(target)
    return fetched
