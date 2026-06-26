"""Tests for the Azure AI Search retriever and the backend factory.

No Azure SDK or network is exercised: a fake ``SupportsSearch`` stands in for the client,
and ``_build_search_client`` is patched where the factory would construct a real one.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import pytest
from iauto_foundry_agent.errors import RetrieverError
from iauto_foundry_agent.retrieval import azure_search as azure_search_module
from iauto_foundry_agent.retrieval.azure_search import AzureAISearchRetriever, SupportsSearch
from iauto_foundry_agent.retrieval.factory import build_retriever
from iauto_foundry_agent.settings import FoundryAgentSettings, RetrieverBackend


class FakeSearchClient:
    """A minimal stand-in for an Azure ``SearchClient``."""

    def __init__(self, rows: list[dict[str, Any]] | Exception) -> None:
        self._rows = rows
        self.calls: list[tuple[str, int]] = []

    def search(self, search_text: str, *, top: int) -> Iterable[Mapping[str, Any]]:
        self.calls.append((search_text, top))
        if isinstance(self._rows, Exception):
            raise self._rows
        return list(self._rows)


def test_maps_rows_to_hits() -> None:
    rows = [
        {
            "id": "k1",
            "title": "VPN",
            "content": "Use GlobalProtect.",
            "source": "Handbook",
            "@search.score": 4.2,
        }
    ]
    retriever = AzureAISearchRetriever(FakeSearchClient(rows))
    hits = retriever.search("vpn", top_k=5)
    assert len(hits) == 1
    assert hits[0].document.id == "k1"
    assert hits[0].document.title == "VPN"
    assert hits[0].document.source == "Handbook"
    assert hits[0].score == pytest.approx(4.2)


def test_respects_custom_field_mapping() -> None:
    rows = [{"key": "k9", "name": "Title", "body": "Body", "ref": "Doc", "@search.score": 1.0}]
    retriever = AzureAISearchRetriever(
        FakeSearchClient(rows),
        id_field="key",
        title_field="name",
        content_field="body",
        source_field="ref",
    )
    hit = retriever.search("q", top_k=1)[0]
    assert hit.document.id == "k9"
    assert hit.document.content == "Body"
    assert hit.document.source == "Doc"


def test_passes_top_k_through() -> None:
    client = FakeSearchClient([])
    AzureAISearchRetriever(client).search("q", top_k=7)
    assert client.calls == [("q", 7)]


def test_non_positive_top_k_short_circuits() -> None:
    client = FakeSearchClient([{"id": "x"}])
    assert AzureAISearchRetriever(client).search("q", top_k=0) == []
    assert client.calls == []


def test_search_errors_are_normalised() -> None:
    retriever = AzureAISearchRetriever(FakeSearchClient(RuntimeError("boom")))
    with pytest.raises(RetrieverError, match="Azure AI Search query failed"):
        retriever.search("q", top_k=1)


def test_from_settings_requires_endpoint() -> None:
    settings = FoundryAgentSettings(retriever_backend=RetrieverBackend.azure_search)
    with pytest.raises(RetrieverError, match="AZURE_SEARCH_ENDPOINT is required"):
        AzureAISearchRetriever.from_settings(settings)


def test_from_settings_builds_with_patched_client(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeSearchClient([{"id": "k1", "title": "t", "content": "c", "@search.score": 1.0}])

    def fake_builder(settings: FoundryAgentSettings) -> SupportsSearch:
        assert settings.azure_search_endpoint == "https://svc.search.windows.net"
        return fake

    monkeypatch.setattr(azure_search_module, "_build_search_client", fake_builder)
    settings = FoundryAgentSettings(
        retriever_backend=RetrieverBackend.azure_search,
        azure_search_endpoint="https://svc.search.windows.net",
    )
    retriever = AzureAISearchRetriever.from_settings(settings)
    assert retriever.search("q", top_k=1)[0].document.id == "k1"


def test_factory_selects_local_by_default() -> None:
    retriever = build_retriever(FoundryAgentSettings())
    # Local BM25 over the bundled KB returns a hit for an in-corpus query.
    assert retriever.search("vpn globalprotect", top_k=1)


def test_factory_selects_azure(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeSearchClient([])
    monkeypatch.setattr(azure_search_module, "_build_search_client", lambda _settings: fake)
    settings = FoundryAgentSettings(
        retriever_backend=RetrieverBackend.azure_search,
        azure_search_endpoint="https://svc.search.windows.net",
    )
    retriever = build_retriever(settings)
    assert isinstance(retriever, AzureAISearchRetriever)
