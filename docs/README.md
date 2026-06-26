# Trainer Kit (Train-the-Trainer)

Everything you need to **deliver and re-teach** *From Power Platform to Azure —
Intelligent Automation with GitHub Agents, Skills & MCP*.

| Document | Use it for |
|---|---|
| **[Agenda](agenda.md)** | The 1-day timetable with pacing guidance |
| **[Prerequisites & setup checklist](prerequisites.md)** | Send to learners ≥3 days before; trainer pre-flight |
| **[Facilitator guide](facilitator-guide.md)** | Narrative, per-lab playbook (timing/failures/talking points/debrief), TTT framing |
| **[Slides](slides/slides.md)** | Marp deck for the instructor-led portions |
| **[Architecture diagram](images/architecture.svg)** | The one-picture course overview |

## The labs (learner content)

| # | Lab | Module B |
|---|---|---|
| 0 | [Setup & modular-inference smoke test](../labs/lab-0-setup/README.md) | prereq |
| 1 | [Discovery, sizing & migration decisioning](../labs/lab-1-discovery-sizing/README.md) | **B.1.2** |
| 2 | [The modular inference layer (Python + .NET)](../labs/lab-2-modular-inference/README.md) | B.1.1 |
| 3 | [Document processing migration](../labs/lab-3-document-processing/README.md) | B.1.1 |
| 4 | [Copilot Studio → Azure AI Foundry agent + RAG](../labs/lab-4-foundry-agent-rag/README.md) | B.1.1 |
| 5 | [Custom MCP server + Copilot agent + skills](../labs/lab-5-mcp-agent-skills/README.md) | B.1.1 |
| 6 | [Hybrid integration + ALM/CI-CD + security](../labs/lab-6-hybrid-alm/README.md) | **B.3.2** |

## Reusable assets

- **Modular inference** — [Python](../src/inference/python/) · [.NET](../src/inference/dotnet/)
- **Discovery & sizing tool** — [`tools/discovery`](../tools/discovery/)
- **Shared infrastructure (Bicep)** — [`infra/bicep`](../infra/bicep/)

> 📋 **Evidence-awareness** runs through the whole kit: each lab flags where its output
> doubles as specialization evidence, so capturing it is a byproduct, not a workstream.
> See the [facilitator guide §5](facilitator-guide.md#5-teaching-the-evidence-awareness-philosophy).
