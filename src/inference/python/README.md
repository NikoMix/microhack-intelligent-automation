# `iauto-inference` (Python)

Modular, provider-agnostic chat inference for **GitHub Models**, **Azure OpenAI**, and
**Azure AI Foundry**. One small API; switch providers with a single environment variable.

This is the Python twin of the .NET [`IAuto.Inference`](../dotnet/) library — both share the
**same environment-variable contract**, so labs can move between languages without re-learning
configuration.

## Why

The labs default to **GitHub Models** because it is **free** and needs only a `GITHUB_TOKEN`.
When you migrate workloads to Azure, flip `INFERENCE_PROVIDER` to `azure_openai` or `foundry`
and **change no code**.

## Install

```bash
uv venv --python 3.12
uv pip install -e ".[azure,dev]"   # 'azure' adds Entra ID auth; 'dev' adds lint/test tooling
```

## Use

```python
from iauto_inference import InferenceClient

client = InferenceClient.from_env()
print(client.complete("Summarise intelligent automation in one sentence.").text)
```

Streaming, async, and message lists are all supported:

```python
for delta in client.stream("Stream me a haiku about Azure"):
    print(delta, end="")

result = await client.acomplete([
    {"role": "system", "content": "You are concise."},
    {"role": "user", "content": "Define RPA."},
])
```

## Configure

| Variable | Provider | Notes |
|---|---|---|
| `INFERENCE_PROVIDER` | all | `github` (default) \| `azure_openai` \| `foundry` |
| `GITHUB_TOKEN` | github | Free models endpoint |
| `GITHUB_MODELS_MODEL` | github | default `openai/gpt-4o-mini` |
| `AZURE_OPENAI_ENDPOINT` / `AZURE_OPENAI_DEPLOYMENT` | azure_openai | API key optional → Entra ID |
| `AZURE_AI_FOUNDRY_ENDPOINT` / `AZURE_AI_FOUNDRY_MODEL` | foundry | API key optional → Entra ID |

See [`.env.example`](.env.example) for the full set.

## Quality gates

```bash
uv run ruff check .
uv run mypy iauto_inference
uv run bandit -c pyproject.toml -r iauto_inference
uv run pytest
```

> 📋 **Evidence awareness:** a clean, provider-portable inference layer is exactly the kind of
> reusable asset an auditor likes to see referenced in a B.1.1 capability statement. Keep the
> repo link handy.
