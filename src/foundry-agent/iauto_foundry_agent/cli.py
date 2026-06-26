"""``iauto-foundry-agent`` — a tiny CLI to exercise the grounded knowledge agent.

Examples::

    # Ask a grounded question (needs an inference provider, e.g. GITHUB_TOKEN)
    iauto-foundry-agent "How do I connect to the VPN?"

    # Preview retrieval only — no model call, no provider needed
    iauto-foundry-agent --show-context "expense policy"

    # List the bundled knowledge base
    iauto-foundry-agent --list
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from iauto_inference.errors import InferenceConfigError, InferenceError

from iauto_foundry_agent.agent import GroundedKnowledgeAgent
from iauto_foundry_agent.documents import load_documents
from iauto_foundry_agent.errors import FoundryAgentError
from iauto_foundry_agent.retrieval.factory import build_retriever
from iauto_foundry_agent.settings import FoundryAgentSettings, RetrieverBackend
from iauto_foundry_agent.telemetry import configure_telemetry


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="iauto-foundry-agent",
        description="Grounded knowledge agent (Microsoft Agent Framework + RAG).",
    )
    parser.add_argument("question", nargs="?", default=None, help="Question to answer.")
    parser.add_argument(
        "--backend",
        choices=[b.value for b in RetrieverBackend],
        default=None,
        help="Override RETRIEVER_BACKEND (local | azure_search).",
    )
    parser.add_argument("--top-k", type=int, default=None, help="Passages to retrieve.")
    parser.add_argument(
        "--show-context",
        action="store_true",
        help="Print retrieved passages instead of calling the model (no provider needed).",
    )
    parser.add_argument(
        "--list", action="store_true", help="List the configured knowledge base and exit."
    )
    return parser


def _settings_from_args(args: argparse.Namespace) -> FoundryAgentSettings:
    settings = FoundryAgentSettings()
    updates: dict[str, object] = {}
    if args.backend is not None:
        updates["retriever_backend"] = RetrieverBackend(args.backend)
    if args.top_k is not None:
        updates["retrieval_top_k"] = args.top_k
    return settings.model_copy(update=updates) if updates else settings


def _print_hits(settings: FoundryAgentSettings, query: str) -> int:
    retriever = build_retriever(settings)
    hits = retriever.search(query, top_k=settings.retrieval_top_k)
    if not hits:
        print("No matching passages found.")
        return 0
    for index, hit in enumerate(hits, start=1):
        citation = hit.document.source or hit.document.id
        print(f"[{index}] {hit.document.title}  (score={hit.score:.3f}, source={citation})")
        print(f"    {hit.document.content}")
    return 0


def _print_kb(settings: FoundryAgentSettings) -> int:
    documents = load_documents(settings.resolved_knowledge_base_path())
    print(f"Knowledge base: {settings.resolved_knowledge_base_path()}  ({len(documents)} docs)")
    for doc in documents:
        tags = f"  [{', '.join(doc.tags)}]" if doc.tags else ""
        print(f"  - {doc.id}: {doc.title}{tags}")
    return 0


def _answer_question(settings: FoundryAgentSettings, question: str) -> int:
    """Build a grounded agent and answer one question, mapping errors to exit codes."""
    try:
        grounded = GroundedKnowledgeAgent.from_env(agent_settings=settings)
        reply = asyncio.run(grounded.ask(question))
    except (FoundryAgentError, InferenceConfigError) as exc:
        print(f"[config error] {exc}", file=sys.stderr)
        return 2
    except InferenceError as exc:
        print(f"[inference error] {exc}", file=sys.stderr)
        return 1
    print(reply.strip())
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code."""
    args = _build_parser().parse_args(argv)
    settings = _settings_from_args(args)

    try:
        configure_telemetry(settings=settings)
    except FoundryAgentError as exc:
        print(f"[config error] {exc}", file=sys.stderr)
        return 2

    if args.list:
        return _print_kb(settings)

    question: str | None = args.question
    if args.show_context:
        if not question:
            print("--show-context requires a query.", file=sys.stderr)
            return 2
        return _print_hits(settings, question)

    if not question:
        _build_parser().print_help(sys.stderr)
        return 2

    return _answer_question(settings, question)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
