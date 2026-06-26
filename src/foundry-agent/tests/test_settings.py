"""Tests for environment-driven settings."""

from __future__ import annotations

from pathlib import Path

import pytest
from iauto_foundry_agent.documents import default_knowledge_base_path
from iauto_foundry_agent.settings import FoundryAgentSettings, RetrieverBackend


def test_defaults_are_local_and_zero_azure() -> None:
    settings = FoundryAgentSettings()
    assert settings.retriever_backend is RetrieverBackend.local
    assert settings.retrieval_top_k == 4
    assert settings.knowledge_base_path is None
    assert settings.azure_search_endpoint is None
    assert settings.resolved_knowledge_base_path() == default_knowledge_base_path()


def test_resolved_knowledge_base_path_honours_override() -> None:
    settings = FoundryAgentSettings(knowledge_base_path="custom/corpus.json")
    assert settings.resolved_knowledge_base_path() == Path("custom/corpus.json")


def test_env_overrides_are_applied(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RETRIEVER_BACKEND", "azure_search")
    monkeypatch.setenv("RETRIEVAL_TOP_K", "9")
    monkeypatch.setenv("AZURE_SEARCH_ENDPOINT", "https://svc.search.windows.net")
    monkeypatch.setenv("AGENT_NAME", "policy-bot")
    settings = FoundryAgentSettings()
    assert settings.retriever_backend is RetrieverBackend.azure_search
    assert settings.retrieval_top_k == 9
    assert settings.azure_search_endpoint == "https://svc.search.windows.net"
    assert settings.agent_name == "policy-bot"


def test_top_k_is_bounded() -> None:
    with pytest.raises(ValueError, match="retrieval_top_k"):
        FoundryAgentSettings(retrieval_top_k=0)
    with pytest.raises(ValueError, match="retrieval_top_k"):
        FoundryAgentSettings(retrieval_top_k=999)


def test_azure_field_mapping_defaults() -> None:
    settings = FoundryAgentSettings()
    assert settings.azure_search_index == "knowledge-index"
    assert settings.azure_search_id_field == "id"
    assert settings.azure_search_content_field == "content"
