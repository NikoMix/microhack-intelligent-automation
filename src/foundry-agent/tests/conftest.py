"""Shared fixtures: a clean environment, sample documents, and a local retriever.

Every test runs provider-free and network-free.
"""

from __future__ import annotations

import pytest
from iauto_foundry_agent.documents import Document
from iauto_foundry_agent.retrieval.local import BM25LocalRetriever

# Env vars that could otherwise leak real configuration into settings-driven tests.
_MANAGED_ENV_VARS = (
    "INFERENCE_PROVIDER",
    "GITHUB_TOKEN",
    "GITHUB_MODELS_ENDPOINT",
    "GITHUB_MODELS_MODEL",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_DEPLOYMENT",
    "AZURE_AI_FOUNDRY_ENDPOINT",
    "AZURE_AI_FOUNDRY_MODEL",
    "AZURE_AI_FOUNDRY_API_KEY",
    "INFERENCE_TIMEOUT",
    "INFERENCE_MAX_RETRIES",
    "RETRIEVER_BACKEND",
    "KNOWLEDGE_BASE_PATH",
    "RETRIEVAL_TOP_K",
    "AGENT_NAME",
    "AGENT_INSTRUCTIONS",
    "AZURE_SEARCH_ENDPOINT",
    "AZURE_SEARCH_INDEX",
    "AZURE_SEARCH_API_KEY",
    "APPLICATIONINSIGHTS_CONNECTION_STRING",
    "OTEL_SERVICE_NAME",
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove managed env vars so settings default deterministically."""
    for name in _MANAGED_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def sample_documents() -> list[Document]:
    """A tiny, deterministic corpus with clearly separable topics."""
    return [
        Document(
            id="d1",
            title="Connecting to the VPN",
            content="Use the GlobalProtect client to connect to the corporate VPN remotely.",
            source="Handbook 3.1",
            tags=("vpn", "remote"),
        ),
        Document(
            id="d2",
            title="Resetting your password",
            content="Reset a forgotten password from the self-service password portal.",
            source="Handbook 2.4",
            tags=("password",),
        ),
        Document(
            id="d3",
            title="Submitting expenses",
            content="Submit expense reports in Concur and attach receipts for review.",
            source="Finance",
            tags=("expenses",),
        ),
    ]


@pytest.fixture
def local_retriever(sample_documents: list[Document]) -> BM25LocalRetriever:
    """A BM25 retriever over the sample corpus."""
    return BM25LocalRetriever(sample_documents)
