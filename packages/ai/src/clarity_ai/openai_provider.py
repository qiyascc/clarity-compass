import base64
import json
from typing import Any

from pydantic import BaseModel, ValidationError

from clarity_ai.provider import Generated, Image, Prompt, ProviderError, RefusalError, Text, Usage


class OpenAICompatibleProvider:
    """Any Chat Completions endpoint with JSON-schema output and image input.

    Covers OpenAI itself and self-hosted vision-language models served through
    an OpenAI-compatible API (vLLM, SGLang, Ollama, LM Studio), such as the
    Qwen-VL family. Install with the `openai` extra.
    """

    name = "openai"

    def __init__(
        self,
        model: str,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        client: Any = None,
    ) -> None:
        if client is None:
            from openai import AsyncOpenAI  # type: ignore[import-not-found]

            client = AsyncOpenAI(base_url=base_url, api_key=api_key or "not-needed")
        self.client = client
        self.model = model

    async def structured[T: BaseModel](self, prompt: Prompt, schema: type[T]) -> Generated[T]:
        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=prompt.max_tokens,
            messages=[
                {"role": "system", "content": prompt.system},
                {"role": "user", "content": [_part(part) for part in prompt.parts]},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "schema": schema.model_json_schema(),
                },
            },
        )
        choice = response.choices[0]
        if getattr(choice.message, "refusal", None):
            raise RefusalError(f"{self.model} declined the request: {choice.message.refusal}")
        if choice.finish_reason == "length":
            raise ProviderError("incomplete output, stop reason length")
        try:
            value = schema.model_validate(json.loads(choice.message.content or ""))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise ProviderError(
                f"{self.model} returned output that does not fit the schema"
            ) from exc

        usage = getattr(response, "usage", None)
        return Generated(
            value=value,
            model=getattr(response, "model", self.model),
            usage=Usage(
                input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                output_tokens=getattr(usage, "completion_tokens", 0) or 0,
            ),
        )


def _part(part: Text | Image) -> dict[str, Any]:
    if isinstance(part, Text):
        return {"type": "text", "text": part.text}
    encoded = base64.standard_b64encode(part.data).decode("ascii")
    return {"type": "image_url", "image_url": {"url": f"data:{part.media_type};base64,{encoded}"}}
