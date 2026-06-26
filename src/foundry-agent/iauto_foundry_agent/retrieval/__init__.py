"""Retrieval backends and the shared :class:`Retriever` protocol."""

from __future__ import annotations

from iauto_foundry_agent.retrieval.azure_search import AzureAISearchRetriever, SupportsSearch
from iauto_foundry_agent.retrieval.base import Retriever, SearchHit, tokenize
from iauto_foundry_agent.retrieval.factory import build_retriever
from iauto_foundry_agent.retrieval.local import BM25LocalRetriever

__all__ = [
    "AzureAISearchRetriever",
    "BM25LocalRetriever",
    "Retriever",
    "SearchHit",
    "SupportsSearch",
    "build_retriever",
    "tokenize",
]
