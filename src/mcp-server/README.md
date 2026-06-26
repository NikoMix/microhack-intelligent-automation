# `iauto-mcp` — intelligent-automation MCP server

A small [Model Context Protocol](https://modelcontextprotocol.io) server (stdio transport,
built on the official Python `mcp` SDK) that exposes **provider-agnostic intelligent-automation
tools**. Every AI-backed tool runs through the shared [`iauto-inference`](../inference/python)
layer, so it works on **GitHub Models** (free default), **Azure OpenAI**, or **Azure AI Foundry**
selected by configuration alone — never by a code change.

This is the capstone artifact for **Lab 5** of the *From Power Platform to Azure — Intelligent
Automation* Train-the-Trainer course (Module **B.1.1**). The full, classroom-ready walkthrough
lives in [`labs/lab-5-mcp-capstone/README.md`](../../labs/lab-5-mcp-capstone/README.md).

## Tools

| Tool | Purpose | Course tie-in |
| --- | --- | --- |
| `summarize_document` | Faithfully summarise a document for a target audience. | Lab 3 (doc intel) |
| `draft_migration_plan` | Draft a structured Power Platform → Azure migration plan. | Capstone |
| `estimate_discovery_sizing` | Deterministic estate sizing/effort math **plus** an optional AI narrative. | Lab 1 (discovery) |
| `answer_with_context` | Answer a question grounded **strictly** in supplied passages (RAG). | Lab 4 (RAG) |

`estimate_discovery_sizing` performs its arithmetic in pure, fully unit-tested code
(`iauto_mcp/sizing.py`); inference is only used for the optional explanation, and can be skipped
entirely (`include_narrative=False`) for an offline, deterministic result.

## Architecture

```
iauto_mcp/
  server.py     FastMCP app + 4 @mcp.tool() wrappers + stdio main()  (thin transport layer)
  tools.py      async tool logic — takes an injected InferenceClient  (unit-testable, no network)
  sizing.py     pure deterministic discovery/sizing heuristics        (no inference, no I/O)
  models.py     pydantic input/output models → rich MCP JSON schemas
  inference.py  lazy, memoised InferenceClient.from_env() factory
  telemetry.py  optional OpenTelemetry tracing (off by default, stderr-safe)
```

The transport layer is deliberately thin: `server.py` only declares the tool surface and
delegates to `tools.py`, whose coroutines accept an `InferenceClient`. That injection point is
what keeps the test suite fast, deterministic, and provider-free.

## Quick start

```bash
# from src/mcp-server
uv venv --python 3.12
uv pip install -e ".[dev]"
cp .env.example .env            # then add a GITHUB_TOKEN (models: read)

uv run iauto-mcp-server         # serve over stdio
uv run mcp dev iauto_mcp/server.py   # …or open the MCP Inspector (needs the [dev] extra)
```

### Configuration

Configuration follows the shared modular-inference contract; copy `.env.example` to `.env`.
The default provider is **GitHub Models** (free). Switch providers by changing
`INFERENCE_PROVIDER` to `azure_openai` or `foundry` and filling in that provider's variables —
no code change. Prefer Entra ID (`DefaultAzureCredential`) over keys for Azure by leaving the
`*_API_KEY` blank. **Never commit `.env`** (it is git-ignored); secrets are passed at runtime.

| Variable | Notes |
| --- | --- |
| `INFERENCE_PROVIDER` | `github` (default) \| `azure_openai` \| `foundry` |
| `GITHUB_TOKEN`, `GITHUB_MODELS_ENDPOINT`, `GITHUB_MODELS_MODEL` | GitHub Models |
| `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY` (optional → Entra), `AZURE_OPENAI_DEPLOYMENT` | Azure OpenAI |
| `AZURE_AI_FOUNDRY_ENDPOINT`, `AZURE_AI_FOUNDRY_MODEL`, `AZURE_AI_FOUNDRY_API_KEY` (optional → Entra) | Azure AI Foundry |
| `INFERENCE_TIMEOUT`, `INFERENCE_MAX_RETRIES` | transport tuning |
| `IAUTO_OTEL_ENABLED` | `1`/`true` to emit OpenTelemetry spans to **stderr** |

> Telemetry never writes to **stdout** — the MCP stdio transport owns that channel for JSON-RPC.

## Quality gates

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict iauto_mcp
uv run bandit -c pyproject.toml -r iauto_mcp
uv run pytest
uv run pip-audit
```

All gates are green and the dependency set carries zero known vulnerabilities. Tests use fakes
that mimic the OpenAI-compatible surface, so they never reach a provider or the network.

## License

MIT. Dependencies are MIT / Apache-2.0 / Microsoft OSS only (license-free to consume).
