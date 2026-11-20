import pytest

from clarity_ai.anthropic_provider import AnthropicProvider
from clarity_ai.factory import create_provider


def test_none_disables_reviews() -> None:
    assert create_provider("none") is None


def test_anthropic_defaults_to_opus() -> None:
    provider = create_provider("anthropic", api_key="sk-test")
    assert isinstance(provider, AnthropicProvider)
    assert provider.model == "claude-opus-5-5"


def test_anthropic_model_can_be_overridden() -> None:
    provider = create_provider("anthropic", api_key="sk-test", model="claude-sonnet-5-5")
    assert provider is not None
    assert provider.model == "claude-sonnet-5-5"


def test_openai_needs_a_model() -> None:
    with pytest.raises(ValueError, match="model"):
        create_provider("openai")


def test_empty_settings_fall_back_to_defaults() -> None:
    provider = create_provider("anthropic", api_key="sk-test", model="", base_url="")
    assert isinstance(provider, AnthropicProvider)
    assert provider.model == "claude-opus-5-5"
    assert str(provider.client.base_url).startswith("https://api.anthropic.com")
