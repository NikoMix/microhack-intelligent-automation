# Python — scaffold a modular-inference capability

Target: **Python 3.12** managed with **uv**. Reuse the shared `iauto-inference` package; never
call a vendor SDK directly in feature code.

## 1. Add the dependency (editable/path dep)

In your component's `pyproject.toml`:

```toml
[project]
dependencies = ["iauto-inference"]

[tool.uv.sources]
iauto-inference = { path = "../inference/python", editable = true }
```

## 2. Write the capability as an injectable coroutine

Accept the client as a parameter so tests can pass a fake. Keep prompts in named constants and
set deliberate generation caps.

```python
from iauto_inference import ChatMessage, ChatResult, InferenceClient

_SYSTEM = "You are a precise assistant. Never invent facts."
_TOKEN_BUDGET = 600
_TEMPERATURE = 0.2

async def classify(client: InferenceClient, *, text: str) -> str:
    """Classify text using whichever provider is configured."""
    result: ChatResult = await client.acomplete(
        [
            ChatMessage(role="system", content=_SYSTEM),
            ChatMessage(role="user", content=f"Classify:\n{text}"),
        ],
        temperature=_TEMPERATURE,
        max_tokens=_TOKEN_BUDGET,
    )
    return result.text.strip()
```

The transport entry point (`InferenceClient.from_env()`) stays at the edge of your app (e.g. an
MCP tool wrapper or a CLI), so the logic above is pure and provider-agnostic.

## 3. Test with a fake — no network, no provider

Inject a fake async client through the public constructor:
`InferenceClient(settings, async_client=fake)`. The fake exposes
`chat.completions.create(**kwargs)` and records calls, so you can assert on the messages sent and
the parsed result. See `src/mcp-server/tests/conftest.py` for a complete, copyable fake.

## 4. Configuration & gates

- Configure only through the shared env contract (`INFERENCE_PROVIDER` + per-provider vars +
  `INFERENCE_TIMEOUT` / `INFERENCE_MAX_RETRIES`). Add new keys to `.env.example` only.
- Run all gates green: `uv run ruff check .`, `uv run ruff format --check .`,
  `uv run mypy --strict <pkg>`, `uv run bandit -c pyproject.toml -r <pkg>`, `uv run pytest`,
  `uv run pip-audit`.
