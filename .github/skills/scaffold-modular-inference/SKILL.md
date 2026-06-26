---
name: scaffold-modular-inference
description: 'Scaffold a new AI capability on the shared modular-inference layer so it runs on GitHub Models, Azure OpenAI, or Azure AI Foundry by configuration only — never a hard-coded provider. Covers Python (iauto-inference, InferenceClient.from_env) and .NET (IAuto.Inference, ChatClientFactory). WHEN: "add an AI feature", "call an LLM from this code", "make this provider-agnostic", "scaffold inference", "summarize/classify/generate with a model", or wiring a new MCP tool that needs inference. DO NOT USE FOR: changing the shared inference layer itself, image generation (GitHub Models is exempt — note it and use Azure OpenAI/Foundry), or non-AI plumbing.'
license: MIT
metadata:
  author: Intelligent Automation TTT
  version: '1.0.0'
---

# Scaffold Modular Inference

> Every AI capability in this repo runs on the **shared inference layer** and switches between
> **GitHub Models** (free default), **Azure OpenAI**, and **Azure AI Foundry** by configuration
> (`INFERENCE_PROVIDER`) — never by code. This skill scaffolds new capabilities that honor that.

## Rules

1. **Never** call a vendor SDK (`openai`, `AzureOpenAIClient`, …) directly in feature code.
   Depend on the shared layer instead.
2. **Inject the client.** Write the capability as a function/method that *takes* a client, so it
   is unit-testable with a fake and never touches the network in tests.
3. **Resolve config from the environment**, not literals. Use the shared env contract
   (`INFERENCE_PROVIDER` + per-provider vars + `INFERENCE_TIMEOUT` / `INFERENCE_MAX_RETRIES`).
4. **Prefer Entra ID** (`DefaultAzureCredential`) over keys for Azure; leave `*_API_KEY` blank to
   opt in. Never commit secrets — use `.env` (git-ignored) + `.env.example`.
5. **Image generation only:** GitHub Models is exempt; fall back to Azure OpenAI / Foundry and
   say so explicitly.

## Choose the language

Match the language already in the folder — do not mix.

| Stack | Package | Entry point | Reference |
| --- | --- | --- | --- |
| Python 3.12 (uv) | `iauto-inference` | `InferenceClient.from_env()` | [python-pattern.md](references/python-pattern.md) |
| .NET (net10.0) | `IAuto.Inference` | `ChatClientFactory.CreateFromEnvironment()` → `IChatClient` | [dotnet-pattern.md](references/dotnet-pattern.md) |

## Steps

1. **Add the dependency** on the shared layer (path/editable dep — never re-implement it).
2. **Write the capability** as an injectable function that accepts the client and returns a typed
   result. Keep prompts in named constants; cap `max_tokens` and set a deliberate `temperature`.
3. **Wire configuration** through the env contract; add any new keys to `.env.example` only.
4. **Test with a fake** that records calls and returns canned replies — assert on the messages
   sent and the parsed result. No network, no provider.
5. **Run the quality gates** for the stack (ruff + mypy --strict + bandit + pip-audit, or the
   .NET analyzer/format/audit equivalents). All green before you finish.

> 📋 Evidence awareness: an assessor would capture the provider-switch proof — the same capability
> producing output under two different `INFERENCE_PROVIDER` values — plus the green gate logs.
> Demonstrate it; do not build evidence-collection tooling.

## Reference index

Load on demand — do not read everything at once:

| Reference | When to load |
| --- | --- |
| [references/python-pattern.md](references/python-pattern.md) | Scaffolding a Python capability |
| [references/dotnet-pattern.md](references/dotnet-pattern.md) | Scaffolding a .NET capability |
