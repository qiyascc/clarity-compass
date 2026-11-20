from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import BaseModel

from clarity_ai.openai_provider import OpenAICompatibleProvider
from clarity_ai.provider import Image, Prompt, ProviderError, RefusalError, Text


class Verdict(BaseModel):
    ok: bool


class FakeCompletions:
    def __init__(self, content: str, finish: str = "stop", refusal: str | None = None) -> None:
        self.reply = SimpleNamespace(
            model="qwen2.5-vl-7b",
            choices=[
                SimpleNamespace(
                    finish_reason=finish,
                    message=SimpleNamespace(content=content, refusal=refusal),
                )
            ],
            usage=SimpleNamespace(prompt_tokens=900, completion_tokens=12),
        )
        self.calls: list[dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return self.reply


def provider(completions: FakeCompletions) -> OpenAICompatibleProvider:
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return OpenAICompatibleProvider("qwen2.5-vl-7b", client=client)


PROMPT = Prompt(system="Review.", parts=[Text("ok?"), Image(b"img", media_type="image/png")])


async def test_sends_images_as_data_urls_and_parses_json() -> None:
    completions = FakeCompletions('{"ok": true}')
    result = await provider(completions).structured(PROMPT, Verdict)
    assert result.value.ok
    assert result.model == "qwen2.5-vl-7b"
    assert result.usage.input_tokens == 900
    call = completions.calls[0]
    assert call["messages"][1]["content"][1]["image_url"]["url"] == "data:image/png;base64,aW1n"
    assert call["response_format"]["json_schema"]["name"] == "Verdict"


async def test_invalid_json_is_reported() -> None:
    with pytest.raises(ProviderError, match="schema"):
        await provider(FakeCompletions('{"ok": "maybe"')).structured(PROMPT, Verdict)


async def test_refusals_and_truncation() -> None:
    with pytest.raises(RefusalError):
        await provider(FakeCompletions("", refusal="no")).structured(PROMPT, Verdict)
    with pytest.raises(ProviderError, match="length"):
        await provider(FakeCompletions("{", finish="length")).structured(PROMPT, Verdict)
