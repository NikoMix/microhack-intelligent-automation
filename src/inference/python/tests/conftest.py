"""Shared fakes so tests never touch the network."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class _Message:
    content: str | None


@dataclass
class _Choice:
    message: _Message | None = None
    delta: _Message | None = None


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
class FakeCompletions:
    """Stand-in for ``client.chat.completions``; records the last call."""

    reply: str = "hello from the fake"
    model: str = "fake-model"
    calls: list[dict[str, Any]] = field(default_factory=list)

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if kwargs.get("stream"):
            return self._stream()
        return _Response(
            choices=[_Choice(message=_Message(content=self.reply))],
            model=self.model,
            usage=_Usage(prompt_tokens=11, completion_tokens=7),
        )

    def _stream(self) -> Any:
        for token in self.reply.split(" "):
            yield _Response(
                choices=[_Choice(delta=_Message(content=token + " "))],
                model=self.model,
            )


@dataclass
class FakeChat:
    completions: FakeCompletions


@dataclass
class FakeClient:
    """Minimal sync OpenAI-compatible client."""

    chat: FakeChat


class FakeAsyncCompletions(FakeCompletions):
    async def create(self, **kwargs: Any) -> Any:  # type: ignore[override]
        self.calls.append(kwargs)
        if kwargs.get("stream"):
            return self._astream()
        return _Response(
            choices=[_Choice(message=_Message(content=self.reply))],
            model=self.model,
            usage=_Usage(prompt_tokens=11, completion_tokens=7),
        )

    async def _astream(self) -> Any:
        for token in self.reply.split(" "):
            yield _Response(
                choices=[_Choice(delta=_Message(content=token + " "))],
                model=self.model,
            )


def make_sync(reply: str = "hello from the fake") -> FakeClient:
    return FakeClient(chat=FakeChat(completions=FakeCompletions(reply=reply)))


def make_async(reply: str = "hello from the fake") -> FakeClient:
    return FakeClient(chat=FakeChat(completions=FakeAsyncCompletions(reply=reply)))
