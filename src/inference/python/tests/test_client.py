"""Tests for :class:`InferenceClient` using injected fakes (no network)."""

from __future__ import annotations

import pytest
from iauto_inference import ChatMessage, InferenceClient, InferenceSettings, Provider
from iauto_inference.client import _normalise
from iauto_inference.errors import InferenceConfigError, InferenceError

from conftest import make_async, make_sync


def _settings(**kw: object) -> InferenceSettings:
    base = {"provider": Provider.github, "github_models_model": "openai/gpt-4o-mini"}
    base.update(kw)
    return InferenceSettings(**base)  # type: ignore[arg-type]


def test_complete_returns_normalised_result() -> None:
    client = InferenceClient(_settings(), sync_client=make_sync("hi there"))
    result = client.complete("hello")
    assert result.text == "hi there"
    assert result.provider == "github"
    assert result.prompt_tokens == 11
    assert result.completion_tokens == 7


def test_complete_uses_default_model_and_passes_params() -> None:
    fake = make_sync()
    client = InferenceClient(_settings(), sync_client=fake)
    client.complete("hello", temperature=0.2, max_tokens=32)
    call = fake.chat.completions.calls[-1]
    assert call["model"] == "openai/gpt-4o-mini"
    assert call["temperature"] == 0.2
    assert call["max_tokens"] == 32
    assert call["messages"] == [{"role": "user", "content": "hello"}]


def test_explicit_model_overrides_default() -> None:
    fake = make_sync()
    client = InferenceClient(_settings(), sync_client=fake)
    client.complete("hi", model="openai/gpt-4o")
    assert fake.chat.completions.calls[-1]["model"] == "openai/gpt-4o"


def test_stream_yields_deltas() -> None:
    client = InferenceClient(_settings(), sync_client=make_sync("a b c"))
    chunks = list(client.stream("hello"))
    assert "".join(chunks).strip() == "a b c"


async def test_acomplete_and_astream() -> None:
    client = InferenceClient(_settings(), async_client=make_async("x y"))
    result = await client.acomplete("hello")
    assert result.text == "x y"
    chunks = [c async for c in client.astream("hello")]
    assert "".join(chunks).strip() == "x y"


def test_missing_model_raises_config_error() -> None:
    client = InferenceClient(
        _settings(provider=Provider.foundry, foundry_model=None), sync_client=make_sync()
    )
    with pytest.raises(InferenceConfigError):
        client.complete("hello")


@pytest.mark.parametrize(
    "messages",
    [
        "hello",
        [{"role": "user", "content": "hello"}],
        [ChatMessage(role="user", content="hello")],
    ],
)
def test_normalise_accepts_supported_shapes(messages: object) -> None:
    assert _normalise(messages) == [{"role": "user", "content": "hello"}]


@pytest.mark.parametrize("bad", [[], [42], [{"role": "user"}]])
def test_normalise_rejects_bad_shapes(bad: object) -> None:
    with pytest.raises(InferenceError):
        _normalise(bad)
