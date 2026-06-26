# Lab 5 — Capstone: Power Platform to Azure with GitHub Agents, Skills & MCP

In this capstone you connect Labs 1–4 into one advisor workflow: Lab 1 discovery sizing, Lab 2 provider-swappable inference, and Labs 3–4 Azure landing patterns exposed through a custom MCP server, a Copilot custom agent, and Copilot skills.

## 1. Start the MCP server

```powershell
cd C:\Users\mixni\.copilot\repos\copilot-worktrees\microhack-intelligent-automation\nikomix-ideal-waddle\src\mcp-server
uv venv --python 3.12
uv pip install -e ".[dev]"
uv run iauto-mcp
```

The server uses stdio by default. It also supports Streamable HTTP for local experimentation:

```powershell
uv run iauto-mcp --transport streamable-http
```

📋 **Evidence awareness — B.1.1 troubleshooting:** Keep the terminal output showing the server start and validation commands. The lab does not collect audit evidence, but trainers should know which commands prove the environment works.

## 2. Register the MCP server with Copilot

Add an MCP entry like this to your Copilot MCP configuration:

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

Restart Copilot CLI or reload VS Code after changing MCP configuration.

## 3. Use the Migration Advisor agent

The agent profile is `.github\agents\migration-advisor.agent.md`. Ask:

> Use the migration-advisor agent to assess this inventory and propose migration waves.

Sample inventory:

```json
[
  {
    "name": "Invoice approval flow",
    "type": "cloud_flow",
    "runs_per_day": 120,
    "avg_minutes": 2.5,
    "connectors": ["SharePoint", "Outlook", "Dataverse"],
    "complexity": "medium",
    "sensitivity": "medium",
    "premium_licensed": true
  },
  {
    "name": "Claims document extraction",
    "type": "ai_builder_doc",
    "runs_per_day": 80,
    "avg_minutes": 4,
    "connectors": 4,
    "complexity": "high",
    "sensitivity": "high",
    "on_prem_dependency": true,
    "premium_licensed": true
  }
]
```

Expected outcome: the advisor calls the MCP tools, cites the discovery sizing, and recommends Azure patterns such as Logic Apps Standard, Azure Functions, Azure AI Document Intelligence, Azure AI Search, or Azure AI Foundry.

## 4. Apply the skills

- `.github\skills\azure-migration-sizing\SKILL.md` guides inventory scoring, ROI, and migration waves.
- `.github\skills\azure-landing-pattern\SKILL.md` guides target pattern selection and security defaults.

Use the skills to explain why each item lands on a given Azure target and how it ties back to the reference architectures practiced in Labs 3–4.

## 5. Swap inference providers

GitHub Models is the default for `summarize_inventory`:

```powershell
$env:INFERENCE_PROVIDER="github"
$env:GITHUB_TOKEN="<token>"
$env:GITHUB_MODELS_MODEL="openai/gpt-4o-mini"
uv run iauto-mcp
```

Switch to Azure OpenAI without code changes:

```powershell
$env:INFERENCE_PROVIDER="azure_openai"
$env:AZURE_OPENAI_ENDPOINT="https://<resource>.openai.azure.com/"
$env:AZURE_OPENAI_DEPLOYMENT="<deployment-name>"
$env:AZURE_OPENAI_API_VERSION="2024-10-21"
uv run iauto-mcp
```

📋 **Evidence awareness — B.1.1 troubleshooting:** If summaries fail, check MCP transport wiring first, then the Python environment, then provider variables. Keep secrets in environment variables or Copilot agent secrets—never in source files.

## Troubleshooting

- **MCP tools do not appear:** restart Copilot, confirm the config path, and verify the server starts with `uv run iauto-mcp`.
- **Broken stdio transport:** remove `print()` debugging; stdio MCP servers must write only JSON-RPC to stdout.
- **Python import errors:** run `uv pip install -e ".[dev]"` from `src\mcp-server` so `iauto-inference` and `iauto-discovery` resolve from local path dependencies.
- **Provider errors:** use `.env.example` as the variable checklist and start with GitHub Models before Azure OpenAI or Foundry.

## Completion criteria

You are done when Copilot can call the MCP tools, the Migration Advisor produces a sized Azure migration recommendation, and the trainer can explain how Lab 5 reuses Labs 1–4 rather than reimplementing them.
