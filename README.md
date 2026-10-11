# From Power Platform to Azure — Intelligent Automation with GitHub Agents, Skills & MCP

A **1-day, classroom-led, hands-on Train-the-Trainer (TTT)** course covering the
buildable **Module B** requirements of the
[Intelligent Automation specialization](https://github.com/NikoMix/specialization-intelligent-automation),
with an **Azure-first** *"migrate Power Platform → Azure"* narrative. It showcases the
latest **GitHub agents, skills, and MCP servers**, all wired to a **modular inference**
layer that runs on **GitHub Models** (free), **Azure OpenAI**, or **Azure AI Foundry**
by configuration alone.

> **Audience:** trainers who will deliver this course, and the automation
> practitioners they teach. **Duration:** ~7 hours of content + breaks.
> **Cost:** designed for free / consumption tiers; each lab notes paid upgrades.

## Agenda (≈7h)

| # | Session | Time | Module B |
|---|---|---|---|
| — | Welcome + Module B framing + architecture tour | 30m | overview |
| 0 | [Setup & modular-inference smoke test](labs/lab-0-setup/) | 45m | prereq |
| 1 | [Discovery & sizing + migration decisioning](labs/lab-1-discovery-sizing/) | 45m | **B.1.2** |
| 2 | [Modular inference layer (Python + .NET)](labs/lab-2-modular-inference/) | 60m | backbone |
| 3 | [Document processing migration (.NET Functions + AI Document Intelligence)](labs/lab-3-document-processing/) | 60m | **B.1.1** |
| 4 | [Copilot Studio → Azure AI Foundry agent + RAG](labs/lab-4-foundry-agent/) | 75m | **B.1.1** |
| 5 | [Custom MCP server + Copilot agent + skills (capstone)](labs/lab-5-mcp-capstone/) | 75m | **B.1.1** |
| 6 | [Hybrid integration + ALM / CI-CD + security](labs/lab-6-hybrid-alm/) | 45m | **B.1.1 / B.3.2** |
| — | Wrap + evidence-awareness recap + TTT debrief | 20m | — |

## What you build

- A **modular inference** library in **both** Python (`iauto-inference`) and .NET
  (`IAuto.Inference`) — one API, three swappable backends.
- An **AI Document Intelligence** pipeline on Azure Functions (the unattended-RPA
  migration target).
- An **Azure AI Foundry** agent with **RAG** over Azure AI Search (the Copilot Studio
  migration target).
- A **custom MCP server**, a **custom GitHub Copilot agent** (`.agent.md`), and reusable
  **skills** — the capstone.
- **Hybrid integration** (APIM → Logic Apps Standard → on-prem) with **Bicep** IaC and a
  **GitHub Actions** ALM pipeline across environments.

## Repository map

```
.github/         Copilot agent + skills, issue templates, CI workflows, copilot-instructions
docs/            TTT kit: facilitator guide, prerequisites, agenda, Marp slides
labs/            lab-0 … lab-6 — self-contained hands-on guides
src/
  inference/     Modular inference backbone — python/ + dotnet/
  document-processing/  Lab 3 (.NET Azure Functions)
  foundry-agent/        Lab 4 (Python, Agent Framework + RAG)
  mcp-server/           Lab 5 (custom MCP server)
  hybrid-integration/   Lab 6 (Logic Apps / APIM / .NET)
tools/discovery/ Lab 1 discovery & sizing / ROI tool
infra/bicep/     Reusable Bicep modules + per-lab deployments
.devcontainer/   Python 3.12 + .NET 10 + uv + func + Azure CLI, ready to go
```

## Prerequisites (short version)

- An **Azure subscription** (free tier is fine) and a **GitHub account** with access to
  **GitHub Models**.
- The **dev container** (recommended) gives you Python 3.12, .NET 10, `uv`, Node, Azure
  CLI, GitHub CLI, `func`, and Bicep with no local setup. Otherwise see
  [`docs/prerequisites.md`](docs/prerequisites.md).

Default inference uses **GitHub Models** — set `GITHUB_TOKEN` and you can run every AI
lab for free, then flip `INFERENCE_PROVIDER=azure_openai` to migrate to Azure.

## Modular inference at a glance

```text
INFERENCE_PROVIDER = github | azure_openai | foundry
```

| Provider | Auth | Use |
|---|---|---|
| GitHub Models (default) | `GITHUB_TOKEN` | Free, in-class |
| Azure OpenAI | Entra ID or key | Production target |
| Azure AI Foundry | Entra ID or key | Foundry catalog |

Feature code depends only on the inference abstraction, so moving from the classroom
to production is a configuration change, not a rewrite.

## For trainers

Start with the [**Facilitator Guide**](docs/facilitator-guide.md): timings, talking
points, common pitfalls, environment reset steps, and the Module B mapping. Instructor
solutions live on the `solutions` branch.

> 📋 **Evidence awareness.** The specialization is assessed on evidence artifacts. This
> course teaches the **buildable** tasks; each lab includes a short *Evidence awareness*
> callout describing what an assessor would capture, without the capture busywork.

## License & dependencies

All dependencies are permissively licensed (MIT / Apache-2.0 / Microsoft OSS) and kept
at their latest secure versions. See [`.github/copilot-instructions.md`](.github/copilot-instructions.md)
for the full engineering bar.