"""Shared fakes so the MCP tool tests never touch a provider or the network.

The fakes mirror the OpenAI-compatible surface that :class:`iauto_inference.InferenceClient`
expects (``client.chat.completions.create(**kwargs)``). We inject them through the public
``InferenceClient(settings, async_client=...)`` constructor, so tests exercise the real
normalisation/await path without any network access.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import pytest
from iauto_inference import InferenceClient
from iauto_inference.settings import InferenceSettings, Provider

ClientFactory = Callable[..., "tuple[InferenceClient, FakeAsyncCompletions]"]


@dataclass
class _Message:
    content: str | None


@dataclass
class _Choice:
    message: _Message | None = None


@dataclass
class _Usage:
    prompt_tokens: int
    completion_tokens: int


@dataclass
class _Response:
    choices: list[_Choice]
    model: str
    usage: _Usage | None = None


@dataclass
class FakeAsyncCompletions:
    """Async stand-in for ``client.chat.completions`` that records every call."""

    reply: str = "fake reply"
    model: str = "fake-model"
    calls: list[dict[str, Any]] = field(default_factory=list)

    async def create(self, **kwargs: Any) -> _Response:
        self.calls.append(kwargs)
        return _Response(
            choices=[_Choice(message=_Message(content=self.reply))],
            model=self.model,
            usage=_Usage(prompt_tokens=13, completion_tokens=5),
        )


@dataclass
class FakeChat:
    completions: FakeAsyncCompletions


@dataclass
class FakeAsyncClient:
    """Minimal async OpenAI-compatible client exposing ``.chat.completions.create``."""

    chat: FakeChat


def make_async_client(reply: str = "fake reply", model: str = "fake-model") -> FakeAsyncClient:
    """Build a fake async client that always returns ``reply``."""
    return FakeAsyncClient(
        chat=FakeChat(completions=FakeAsyncCompletions(reply=reply, model=model))
    )


def build_client(
    reply: str = "fake reply",
    *,
    provider: Provider = Provider.github,
    model: str = "fake-model",
) -> tuple[InferenceClient, FakeAsyncCompletions]:
    """Return an :class:`InferenceClient` wired to a fake plus its completions recorder."""
    fake = make_async_client(reply=reply, model=model)
    settings = InferenceSettings(
        provider=provider,
        github_models_model="openai/gpt-4o-mini",
        azure_openai_deployment="gpt-4o-mini",
        foundry_model="gpt-4o-mini",
    )
    client = InferenceClient(settings, async_client=fake)
    return client, fake.chat.completions


@pytest.fixture
def make_client() -> ClientFactory:
    """Fixture factory: ``client, completions = make_client(reply=...)``.

    Exposed as a fixture (not a plain import) because the editable ``iauto-inference`` install
    puts its own ``tests`` package on ``sys.path``; importing ``tests.conftest`` would collide.
    """
    return build_client
