"""Factories that build *real* ``openai`` response objects for offline agent tests.

Using the genuine ``openai.types`` models (rather than ad-hoc fakes) means the Agent
Framework parses exactly what it would in production, so the function-calling loop is
exercised faithfully — without any network or provider.
"""

from __future__ import annotations

from collections.abc import Sequence

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)
from openai.types.completion_usage import CompletionUsage

_USAGE = CompletionUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2)


def tool_call_completion(
    name: str, arguments: str, *, call_id: str = "call_1", model: str = "test-model"
) -> ChatCompletion:
    """A completion whose single choice asks to call ``name`` with JSON ``arguments``."""
    message = ChatCompletionMessage(
        role="assistant",
        content=None,
        tool_calls=[
            ChatCompletionMessageToolCall(
                id=call_id,
                type="function",
                function=Function(name=name, arguments=arguments),
            )
        ],
    )
    return ChatCompletion(
        id="chatcmpl-tool",
        object="chat.completion",
        created=0,
        model=model,
        choices=[Choice(index=0, finish_reason="tool_calls", message=message)],
        usage=_USAGE,
    )


def text_completion(content: str, *, model: str = "test-model") -> ChatCompletion:
    """A normal assistant completion that finishes with ``content``."""
    message = ChatCompletionMessage(role="assistant", content=content)
    return ChatCompletion(
        id="chatcmpl-final",
        object="chat.completion",
        created=0,
        model=model,
        choices=[Choice(index=0, finish_reason="stop", message=message)],
        usage=_USAGE,
    )


class RecordingAsyncOpenAI:
    """Wrap an ``AsyncOpenAI`` whose ``chat.completions.create`` replays queued responses."""

    def __init__(self, responses: Sequence[ChatCompletion]) -> None:
        self.client = AsyncOpenAI(api_key="dummy-key", base_url="http://localhost:9999/v1")
        self._queue: list[ChatCompletion] = list(responses)
        self.calls: list[dict[str, object]] = []

        async def _create(*_args: object, **kwargs: object) -> ChatCompletion:
            self.calls.append(kwargs)
            if not self._queue:  # pragma: no cover - defensive
                raise AssertionError("No more queued completions for create().")
            return self._queue.pop(0)

        # Shadow the bound method with our async stub — no network is ever touched.
        self.client.chat.completions.create = _create  # type: ignore[method-assign]


def make_stub_client(responses: Sequence[ChatCompletion]) -> RecordingAsyncOpenAI:
    """Convenience builder for a queue-replaying AsyncOpenAI stub."""
    return RecordingAsyncOpenAI(responses)
