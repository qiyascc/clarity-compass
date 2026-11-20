import base64
from types import SimpleNamespace
from typing import Any

import anthropic
import httpx2 as httpx
import pytest
from pydantic import BaseModel

from clarity_ai.anthropic_provider import AnthropicProvider
from clarity_ai.provider import Image, Prompt, ProviderError, RefusalError, Text


class Verdict(BaseModel):
    ok: bool


class FakeMessages:
    def __init__(self, response: Any = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.calls: list[dict[str, Any]] = []

    async def parse(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


def client(messages: FakeMessages) -> anthropic.AsyncAnthropic:
    return SimpleNamespace(beta=SimpleNamespace(messages=messages))  # type: ignore[return-value]


def response(stop_reason: str = "end_turn", parsed: Any = None) -> SimpleNamespace:
    return SimpleNamespace(
        stop_reason=stop_reason,
        stop_details=SimpleNamespace(category="cyber") if stop_reason == "refusal" else None,
        parsed_output=parsed,
        model="claude-opus-5-5",
        usage=SimpleNamespace(input_tokens=1200, output_tokens=80, cache_read_input_tokens=1000),
    )


PROMPT = Prompt(
    system="You review websites.",
    parts=[Text("Is this fine?"), Image(b"\xff\xd8jpeg", label="hero")],
    effort="medium",
)


async def test_builds_a_structured_request_with_images_and_fallbacks() -> None:
    messages = FakeMessages(response(parsed=Verdict(ok=True)))
    result = await AnthropicProvider(client(messages)).structured(PROMPT, Verdict)

    assert result.value.ok
    assert result.usage.cache_read_tokens == 1000
    call = messages.calls[0]
    assert call["model"] == "claude-opus-5-5"
    assert call["output_format"] is Verdict
    assert call["output_config"] == {"effort": "medium"}
    assert call["fallbacks"] == "default"
    assert call["betas"] == ["server-side-fallback-2026-07-01"]
    assert call["system"][0]["cache_control"] == {"type": "ephemeral"}
    text, image = call["messages"][0]["content"]
    assert text == {"type": "text", "text": "Is this fine?"}
    assert base64.b64decode(image["source"]["data"]) == b"\xff\xd8jpeg"


async def test_fallbacks_can_be_disabled() -> None:
    messages = FakeMessages(response(parsed=Verdict(ok=True)))
    await AnthropicProvider(client(messages), fallbacks=False).structured(PROMPT, Verdict)
    assert "fallbacks" not in messages.calls[0]


async def test_refusal_raises() -> None:
    messages = FakeMessages(response("refusal"))
    with pytest.raises(RefusalError, match="cyber"):
        await AnthropicProvider(client(messages)).structured(PROMPT, Verdict)


async def test_truncated_output_raises() -> None:
    messages = FakeMessages(response("max_tokens"))
    with pytest.raises(ProviderError, match="max_tokens"):
        await AnthropicProvider(client(messages)).structured(PROMPT, Verdict)


async def test_api_errors_are_wrapped() -> None:
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    error = anthropic.RateLimitError(
        "slow down", response=httpx.Response(429, request=request), body=None
    )
    with pytest.raises(ProviderError, match="429"):
        await AnthropicProvider(client(FakeMessages(error=error))).structured(PROMPT, Verdict)
