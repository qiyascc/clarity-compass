import base64
from typing import Any

import anthropic
from anthropic.types.beta import BetaImageBlockParam, BetaMessageParam, BetaTextBlockParam
from pydantic import BaseModel, ValidationError

from clarity_ai.provider import Generated, Image, Prompt, ProviderError, RefusalError, Text, Usage

DEFAULT_MODEL = "claude-opus-5-5"
FALLBACK_BETA = "server-side-fallback-2026-07-01"


class AnthropicProvider:
    """Claude through the Messages API with structured outputs.

    Policy refusals are retried server-side on a fallback model chosen by the
    API (`fallbacks="default"`); a refusal by the whole chain raises.
    """

    name = "anthropic"

    def __init__(
        self,
        client: anthropic.AsyncAnthropic | None = None,
        *,
        model: str = DEFAULT_MODEL,
        fallbacks: bool = True,
    ) -> None:
        self.client = client or anthropic.AsyncAnthropic()
        self.model = model
        self.fallbacks = fallbacks

    async def structured[T: BaseModel](self, prompt: Prompt, schema: type[T]) -> Generated[T]:
        message: BetaMessageParam = {
            "role": "user",
            "content": [_block(part) for part in prompt.parts],
        }
        extra: dict[str, Any] = {}
        if self.fallbacks:
            extra = {"betas": [FALLBACK_BETA], "fallbacks": "default"}
        try:
            response = await self.client.beta.messages.parse(
                model=self.model,
                max_tokens=prompt.max_tokens,
                system=[
                    {"type": "text", "text": prompt.system, "cache_control": {"type": "ephemeral"}}
                ],
                messages=[message],
                output_config={"effort": prompt.effort},
                output_format=schema,
                **extra,
            )
        except anthropic.APIStatusError as exc:
            raise ProviderError(
                f"Claude request failed with {exc.status_code}: {exc.message}"
            ) from exc
        except anthropic.APIConnectionError as exc:
            raise ProviderError("Claude is unreachable") from exc
        except ValidationError as exc:
            # The SDK parses eagerly, so output cut off at max_tokens fails here.
            raise ProviderError("incomplete structured output (unparseable JSON)") from exc

        if response.stop_reason == "refusal":
            category = getattr(response.stop_details, "category", None)
            raise RefusalError(f"Claude declined the request ({category or 'unspecified'})")
        if response.stop_reason == "max_tokens" or response.parsed_output is None:
            raise ProviderError(
                f"incomplete structured output (stop reason {response.stop_reason})"
            )

        usage = response.usage
        return Generated(
            value=response.parsed_output,
            model=response.model,
            usage=Usage(
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                cache_read_tokens=usage.cache_read_input_tokens or 0,
            ),
        )


def _block(part: Text | Image) -> BetaTextBlockParam | BetaImageBlockParam:
    if isinstance(part, Text):
        return {"type": "text", "text": part.text}
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": part.media_type,
            "data": base64.standard_b64encode(part.data).decode("ascii"),
        },
    }
