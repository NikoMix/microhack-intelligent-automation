"""Retriever selection: build the right backend from settings."""

from __future__ import annotations

from iauto_foundry_agent.retrieval.azure_search import AzureAISearchRetriever
from iauto_foundry_agent.retrieval.base import Retriever
from iauto_foundry_agent.retrieval.local import BM25LocalRetriever
from iauto_foundry_agent.settings import FoundryAgentSettings, RetrieverBackend


def build_retriever(settings: FoundryAgentSettings) -> Retriever:
    """Construct the retriever named by ``settings.retriever_backend``."""
    if settings.retriever_backend is RetrieverBackend.azure_search:
        return AzureAISearchRetriever.from_settings(settings)
    return BM25LocalRetriever.from_path(settings.resolved_knowledge_base_path())
