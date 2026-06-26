"""Tests for Azure AI Search index provisioning.

No Azure SDK or network is exercised: fake admin/upload clients stand in for the Azure
``SearchIndexClient`` / ``SearchClient``, and ``_build_index_definition`` is patched out where the
real index model would otherwise be constructed. One opt-in test imports the Azure models to verify
the index field shape, skipped automatically when the ``azure`` extra is absent.
"""

from __future__ import annotations

from typing import Any

import pytest
from iauto_foundry_agent import indexing
from iauto_foundry_agent.documents import Document
from iauto_foundry_agent.errors import RetrieverError
from iauto_foundry_agent.indexing import build_documents_payload, provision_index
from iauto_foundry_agent.settings import FoundryAgentSettings

_ENDPOINT = "https://svc.search.windows.net"


class FakeIndexAdmin:
    """Minimal stand-in for an Azure ``SearchIndexClient``."""

    def __init__(self, *, create_error: Exception | None = None) -> None:
        self.created: list[Any] = []
        self.deleted: list[Any] = []
        self._create_error = create_error

    def create_or_update_index(self, index: Any) -> Any:
        if self._create_error is not None:
            raise self._create_error
        self.created.append(index)
        return index

    def delete_index(self, index: Any) -> None:
        self.deleted.append(index)


class FakeUploader:
    """Minimal stand-in for an Azure ``SearchClient`` upload surface."""

    def __init__(self, *, upload_error: Exception | None = None) -> None:
        self.uploaded: list[list[Any]] = []
        self._upload_error = upload_error

    def upload_documents(self, documents: Any) -> Any:
        if self._upload_error is not None:
            raise self._upload_error
        rows = list(documents)
        self.uploaded.append(rows)
        return [{"status": True} for _ in rows]


def _azure_settings(**overrides: Any) -> FoundryAgentSettings:
    return FoundryAgentSettings(
        azure_search_endpoint=_ENDPOINT, azure_search_index="kb", **overrides
    )


def test_payload_maps_default_fields(sample_documents: list[Document]) -> None:
    payload = build_documents_payload(FoundryAgentSettings(), sample_documents)
    assert payload[0] == {
        "id": "d1",
        "title": "Connecting to the VPN",
        "content": "Use the GlobalProtect client to connect to the corporate VPN remotely.",
        "source": "Handbook 3.1",
        "tags": ["vpn", "remote"],
    }


def test_payload_handles_missing_source() -> None:
    docs = [Document(id="x", title="T", content="C", source=None)]
    payload = build_documents_payload(FoundryAgentSettings(), docs)
    assert payload[0]["source"] == ""
    assert payload[0]["tags"] == []


def test_payload_respects_custom_field_mapping(sample_documents: list[Document]) -> None:
    settings = FoundryAgentSettings(
        azure_search_id_field="key",
        azure_search_title_field="name",
        azure_search_content_field="body",
        azure_search_source_field="ref",
    )
    row = build_documents_payload(settings, sample_documents)[0]
    assert row["key"] == "d1"
    assert row["name"] == "Connecting to the VPN"
    assert row["body"].startswith("Use the GlobalProtect")
    assert row["ref"] == "Handbook 3.1"


def test_provision_creates_index_and_uploads(
    monkeypatch: pytest.MonkeyPatch, sample_documents: list[Document]
) -> None:
    monkeypatch.setattr(indexing, "_build_index_definition", lambda _s: "INDEX_DEF")
    admin = FakeIndexAdmin()
    uploader = FakeUploader()
    count = provision_index(
        _azure_settings(),
        documents=sample_documents,
        index_client=admin,
        search_client=uploader,
    )
    assert count == 3
    assert admin.created == ["INDEX_DEF"]
    assert admin.deleted == []
    assert len(uploader.uploaded[0]) == 3
    assert uploader.uploaded[0][0]["id"] == "d1"


def test_provision_recreate_deletes_first(
    monkeypatch: pytest.MonkeyPatch, sample_documents: list[Document]
) -> None:
    monkeypatch.setattr(indexing, "_build_index_definition", lambda _s: "INDEX_DEF")
    admin = FakeIndexAdmin()
    provision_index(
        _azure_settings(),
        documents=sample_documents,
        recreate=True,
        index_client=admin,
        search_client=FakeUploader(),
    )
    assert admin.deleted == ["kb"]
    assert admin.created == ["INDEX_DEF"]


def test_provision_defaults_to_bundled_kb(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(indexing, "_build_index_definition", lambda _s: "INDEX_DEF")
    uploader = FakeUploader()
    count = provision_index(
        _azure_settings(), index_client=FakeIndexAdmin(), search_client=uploader
    )
    assert count == len(uploader.uploaded[0])
    assert count >= 10  # the bundled sample KB


def test_provision_requires_endpoint(sample_documents: list[Document]) -> None:
    with pytest.raises(RetrieverError, match="AZURE_SEARCH_ENDPOINT is required"):
        provision_index(FoundryAgentSettings(), documents=sample_documents)


def test_provision_normalises_create_error(
    monkeypatch: pytest.MonkeyPatch, sample_documents: list[Document]
) -> None:
    monkeypatch.setattr(indexing, "_build_index_definition", lambda _s: "INDEX_DEF")
    admin = FakeIndexAdmin(create_error=RuntimeError("nope"))
    with pytest.raises(RetrieverError, match="Could not create the Azure AI Search index"):
        provision_index(
            _azure_settings(),
            documents=sample_documents,
            index_client=admin,
            search_client=FakeUploader(),
        )


def test_provision_normalises_upload_error(
    monkeypatch: pytest.MonkeyPatch, sample_documents: list[Document]
) -> None:
    monkeypatch.setattr(indexing, "_build_index_definition", lambda _s: "INDEX_DEF")
    uploader = FakeUploader(upload_error=RuntimeError("boom"))
    with pytest.raises(RetrieverError, match="Could not upload documents"):
        provision_index(
            _azure_settings(),
            documents=sample_documents,
            index_client=FakeIndexAdmin(),
            search_client=uploader,
        )


def test_index_definition_field_shape() -> None:
    pytest.importorskip("azure.search.documents.indexes.models")
    index = indexing._build_index_definition(FoundryAgentSettings())
    assert index.name == "knowledge-index"
    names = {field.name for field in index.fields}
    assert names == {"id", "title", "content", "source", "tags"}
    key_fields = [field.name for field in index.fields if field.key]
    assert key_fields == ["id"]


def test_main_reports_count(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("AZURE_SEARCH_ENDPOINT", _ENDPOINT)

    def fake_provision(settings: FoundryAgentSettings, **_kwargs: Any) -> int:
        return 7

    monkeypatch.setattr(indexing, "provision_index", fake_provision)
    assert indexing.main([]) == 0
    assert "7 documents" in capsys.readouterr().out


def test_main_maps_errors_to_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AZURE_SEARCH_ENDPOINT", _ENDPOINT)

    def fake_provision(settings: FoundryAgentSettings, **_kwargs: Any) -> int:
        raise RetrieverError("boom")

    monkeypatch.setattr(indexing, "provision_index", fake_provision)
    assert indexing.main([]) == 2
