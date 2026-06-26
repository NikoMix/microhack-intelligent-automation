"""Command line entry point for the Lab 4 Foundry RAG agent."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import NoReturn

from dotenv import load_dotenv

from iauto_foundry_agent.agent import FoundryRagAgent
from iauto_foundry_agent.ingestion import ingest_sample_knowledge
from iauto_foundry_agent.retrieval import SearchClientFactory
from iauto_foundry_agent.settings import Settings
from iauto_foundry_agent.summarizer import ContextSummarizer
from iauto_foundry_agent.telemetry import configure_telemetry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="iauto-foundry",
        description="Migrate a Copilot Studio knowledge agent to Azure AI Foundry + Search RAG.",
    )
    parser.add_argument("--env-file", default=".env", help="Optional .env file to load.")
    subcommands = parser.add_subparsers(dest="command", required=True)

    ingest = subcommands.add_parser(
        "ingest",
        help="Create the Search index and upload sample KB docs.",
    )
    ingest.add_argument(
        "--data-dir",
        type=Path,
        help="Optional directory containing markdown files.",
    )

    ask = subcommands.add_parser("ask", help="Ask a grounded knowledge-base question.")
    ask.add_argument("question", help="Question to answer from the migrated knowledge base.")
    ask.add_argument(
        "--show-context",
        action="store_true",
        help="Print the raw retrieved context after the answer.",
    )
    return parser


async def _run_async(args: argparse.Namespace) -> int:
    load_dotenv(args.env_file)
    settings = Settings.from_env()
    configure_telemetry(settings.app_insights_connection_string)

    if args.command == "ingest":
        count = await ingest_sample_knowledge(settings, args.data_dir)
        print(f"Uploaded {count} sample knowledge chunks to index '{settings.search_index}'.")
        return 0

    if args.command == "ask":
        factory = SearchClientFactory(settings)
        try:
            retriever = factory.retriever()
            runner = FoundryRagAgent(settings, retriever, ContextSummarizer())
            result = await runner.answer(args.question)
            print(result.format_for_cli())
            if args.show_context:
                print("\nRetrieved context:\n" + result.retrieval.format_context())
        finally:
            await factory.close()
        return 0

    _die(f"Unknown command: {args.command}")


def _die(message: str) -> NoReturn:
    raise SystemExit(message)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_run_async(args)))


if __name__ == "__main__":
    main()
