from typing import Literal

import anthropic

from clarity_ai.anthropic_provider import DEFAULT_MODEL, AnthropicProvider
from clarity_ai.openai_provider import OpenAICompatibleProvider
from clarity_ai.provider import LLMProvider

ProviderKind = Literal["anthropic", "openai", "none"]


def create_provider(
    kind: ProviderKind,
    *,
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
) -> LLMProvider | None:
    if kind == "none":
        return None
    if kind == "anthropic":
        client = anthropic.AsyncAnthropic(api_key=api_key, base_url=base_url)
        return AnthropicProvider(client, model=model or DEFAULT_MODEL)
    if not model:
        raise ValueError("the openai provider needs a model name")
    return OpenAICompatibleProvider(model, base_url=base_url, api_key=api_key)
