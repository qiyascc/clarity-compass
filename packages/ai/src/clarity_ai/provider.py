from dataclasses import dataclass, field
from typing import Literal, Protocol

from pydantic import BaseModel

Effort = Literal["low", "medium", "high", "xhigh", "max"]


@dataclass(frozen=True)
class Text:
    text: str


@dataclass(frozen=True)
class Image:
    data: bytes
    media_type: Literal["image/png", "image/jpeg", "image/webp"] = "image/jpeg"
    label: str | None = None


Part = Text | Image


@dataclass(frozen=True)
class Prompt:
    system: str
    parts: list[Part]
    max_tokens: int = 16_000
    effort: Effort = "high"


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0


@dataclass(frozen=True)
class Generated[T: BaseModel]:
    value: T
    model: str
    usage: Usage = field(default_factory=Usage)


class ProviderError(RuntimeError):
    pass


class RefusalError(ProviderError):
    pass


class LLMProvider(Protocol):
    name: str
    model: str

    async def structured[T: BaseModel](self, prompt: Prompt, schema: type[T]) -> Generated[T]: ...
