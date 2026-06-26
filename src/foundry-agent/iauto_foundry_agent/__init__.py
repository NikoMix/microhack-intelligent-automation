"""Copilot Studio → Azure AI Foundry agent with RAG, on the modular inference layer.

Public surface:

* :class:`GroundedKnowledgeAgent` / :func:`build_agent` / :func:`answer` — the agent.
* :class:`Document` / :func:`load_documents` — the knowledge-base corpus.
* :class:`BM25LocalRetriever` / :class:`AzureAISearchRetriever` / :func:`build_retriever` — RAG.
* :class:`FoundryAgentSettings` — configuration (backend selection, top-k, Azure Search, telemetry).
"""

from __future__ import annotations

from iauto_foundry_agent import _compat  # noqa: F401  # isort:skip  (must precede agent_framework imports)
from iauto_foundry_agent.agent import (
    DEFAULT_INSTRUCTIONS,
    GroundedKnowledgeAgent,
    answer,
    build_agent,
    build_chat_client,
    format_context,
    make_search_tool,
)
from iauto_foundry_agent.documents import Document, load_documents, parse_documents
from iauto_foundry_agent.errors import (
    FoundryAgentError,
    KnowledgeBaseError,
    RetrieverError,
)
from iauto_foundry_agent.indexing import build_documents_payload, provision_index
from iauto_foundry_agent.retrieval import (
    AzureAISearchRetriever,
    BM25LocalRetriever,
    Retriever,
    SearchHit,
    build_retriever,
)
from iauto_foundry_agent.settings import FoundryAgentSettings, RetrieverBackend
from iauto_foundry_agent.telemetry import configure_telemetry

__all__ = [
    "DEFAULT_INSTRUCTIONS",
    "AzureAISearchRetriever",
    "BM25LocalRetriever",
    "Document",
    "FoundryAgentError",
    "FoundryAgentSettings",
    "GroundedKnowledgeAgent",
    "KnowledgeBaseError",
    "Retriever",
    "RetrieverBackend",
    "RetrieverError",
    "SearchHit",
    "answer",
    "build_agent",
    "build_chat_client",
    "build_documents_payload",
    "build_retriever",
    "configure_telemetry",
    "format_context",
    "load_documents",
    "make_search_tool",
    "parse_documents",
    "provision_index",
]

__version__ = "0.1.0"
