"""The :class:`InferenceClient` facade -- one API across all providers."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from iauto_inference.errors import InferenceConfigError, InferenceError
from iauto_inference.providers import build_clients
from iauto_inference.settings import InferenceSettings

if TYPE_CHECKING:  # pragma: no cover - typing only
    from iauto_inference.settings import Provider

MessageInput = "Sequence[ChatMessage] | Sequence[Mapping[str, str]] | str"


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """A single chat message."""

    role: str
    content: str

    def as_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass(frozen=True, slots=True)
class ChatResult:
    """Normalised completion result, provider-agnostic."""

    text: str
    model: str
    provider: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    raw: Any = None


def _normalise(messages: Any) -> list[dict[str, str]]:
    """Accept a string, dicts, or :class:`ChatMessage` and return wire-format dicts."""
    if isinstance(messages, str):
        return [{"role": "user", "content": messages}]
    if not isinstance(messages, Sequence) or not messages:
        raise InferenceError("messages must be a non-empty string or sequence.")
    out: list[dict[str, str]] = []
    for m in messages:
        if isinstance(m, ChatMessage):
            out.append(m.as_dict())
        elif isinstance(m, Mapping) and "role" in m and "content" in m:
            out.append({"role": str(m["role"]), "content": str(m["content"])})
        else:
            raise InferenceError(
                "Each message must be a ChatMessage or a mapping with 'role' and 'content'."
            )
    return out


class InferenceClient:
    """Provider-agnostic chat client.

    Build from the environment::

        client = InferenceClient.from_env()
        print(client.complete("Say hello").text)

    Or inject settings / a pre-built client (used in tests and advanced wiring).
    """

    def __init__(
        self,
        settings: InferenceSettings | None = None,
        *,
        sync_client: Any | None = None,
        async_client: Any | None = None,
    ) -> None:
        self._settings = settings or InferenceSettings()
        if sync_client is not None or async_client is not None:
            self._sync = sync_client
            self._async = async_client
        else:
            self._sync, self._async = build_clients(self._settings)

    @classmethod
    def from_env(cls) -> InferenceClient:
        """Construct from environment variables / ``.env``."""
        return cls(InferenceSettings())

    @property
    def provider(self) -> Provider:
        return self._settings.provider

    @property
    def raw_client(self) -> Any:
        """Underlying OpenAI-compatible sync client (e.g. to hand to an agent framework)."""
        if self._sync is None:
            raise InferenceConfigError("No synchronous client is configured.")
        return self._sync

    @property
    def raw_async_client(self) -> Any:
        if self._async is None:
            raise InferenceConfigError("No asynchronous client is configured.")
        return self._async

    def _model(self, model: str | None) -> str:
        resolved = model or self._settings.default_model()
        if not resolved:
            raise InferenceConfigError(
                f"No model configured for provider '{self._settings.provider.value}'. "
                f"Pass model=... or set the provider's model/deployment env var."
            )
        return resolved

    def _params(
        self, messages: Any, model: str | None, temperature: float | None,
        max_tokens: int | None, extra: dict[str, Any],
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "model": self._model(model),
            "messages": _normalise(messages),
        }
        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        params.update(extra)
        return params

    def _to_result(self, response: Any, model: str) -> ChatResult:
        choice = response.choices[0]
        usage = getattr(response, "usage", None)
        return ChatResult(
            text=(choice.message.content or ""),
            model=getattr(response, "model", model),
            provider=self._settings.provider.value,
            prompt_tokens=getattr(usage, "prompt_tokens", None),
            completion_tokens=getattr(usage, "completion_tokens", None),
            raw=response,
        )

    def complete(
        self,
        messages: Any,
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **extra: Any,
    ) -> ChatResult:
        """Synchronous chat completion."""
        params = self._params(messages, model, temperature, max_tokens, extra)
        response = self.raw_client.chat.completions.create(**params)
        return self._to_result(response, params["model"])

    async def acomplete(
        self,
        messages: Any,
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **extra: Any,
    ) -> ChatResult:
        """Asynchronous chat completion."""
        params = self._params(messages, model, temperature, max_tokens, extra)
        response = await self.raw_async_client.chat.completions.create(**params)
        return self._to_result(response, params["model"])

    def stream(
        self,
        messages: Any,
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **extra: Any,
    ) -> Iterator[str]:
        """Yield content deltas as they arrive (synchronous)."""
        params = self._params(messages, model, temperature, max_tokens, extra)
        params["stream"] = True
        for chunk in self.raw_client.chat.completions.create(**params):
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content

    async def astream(
        self,
        messages: Any,
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **extra: Any,
    ) -> AsyncIterator[str]:
        """Yield content deltas as they arrive (asynchronous)."""
        params = self._params(messages, model, temperature, max_tokens, extra)
        params["stream"] = True
        stream = await self.raw_async_client.chat.completions.create(**params)
        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content
