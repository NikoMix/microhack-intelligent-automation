"""Typed error hierarchy for the Foundry agent / RAG layer."""

from __future__ import annotations


class FoundryAgentError(Exception):
    """Base error for all Foundry-agent failures.

    Carries an actionable message so learners can self-correct in the labs.
    """


class KnowledgeBaseError(FoundryAgentError):
    """Raised when the knowledge-base corpus is missing or malformed."""


class RetrieverError(FoundryAgentError):
    """Raised when a retriever cannot be built or a search fails."""
