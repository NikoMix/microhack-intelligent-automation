# Intelligent Automation MCP Server

Custom Model Context Protocol (MCP) server for Lab 5. It exposes deterministic Power Platform → Azure migration sizing from `iauto-discovery` and an executive summary powered by the shared `iauto-inference` provider abstraction.

## Tools

- `assess_migration` — sizes one automation and returns Azure target, effort, security notes, and indicative cost.
- `recommend_azure_target` — maps an automation type to an Azure landing pattern and reference architecture.
- `summarize_inventory` — builds a discovery report and generates an executive summary via GitHub Models, Azure OpenAI, or Azure AI Foundry.
- `estimate_roi` — surfaces the discovery ROI heuristic for a portfolio.

## Run locally

```powershell
cd C:\Users\mixni\.copilot\repos\copilot-worktrees\microhack-intelligent-automation\nikomix-ideal-waddle\src\mcp-server
uv venv --python 3.12
uv pip install -e ".[dev]"
uv run iauto-mcp
```

The default transport is `stdio`. Logs go to stderr so stdout remains valid MCP JSON-RPC. For local experimentation with Streamable HTTP:

```powershell
uv run iauto-mcp --transport streamable-http
```

## Copilot MCP configuration

```json
{
  "mcpServers": {
    "iauto-migration": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\mixni\\.copilot\\repos\\copilot-worktrees\\microhack-intelligent-automation\\nikomix-ideal-waddle\\src\\mcp-server",
        "run",
        "iauto-mcp"
      ],
      "env": {
        "INFERENCE_PROVIDER": "github",
        "GITHUB_TOKEN": "${input:github_token}"
      }
    }
  }
}
```

## Validate

```powershell
uv run ruff check .
uv run mypy iauto_mcp
uv run bandit -c pyproject.toml -r iauto_mcp
uv run pytest
uv run pip-audit
```
