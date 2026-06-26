"""Tests for the knowledge-base document model and loader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from iauto_foundry_agent.documents import (
    Document,
    default_knowledge_base_path,
    load_documents,
    parse_documents,
)
from iauto_foundry_agent.errors import KnowledgeBaseError


def test_searchable_text_joins_title_and_content() -> None:
    doc = Document(id="x", title="Title", content="Body text")
    assert doc.searchable_text == "Title\nBody text"


def test_document_is_frozen() -> None:
    doc = Document(id="x", title="t", content="c")
    with pytest.raises(AttributeError):
        doc.title = "other"  # type: ignore[misc]


def test_default_knowledge_base_exists_and_loads() -> None:
    path = default_knowledge_base_path()
    assert path.exists()
    docs = load_documents(path)
    assert len(docs) >= 5
    assert all(d.id and d.title and d.content for d in docs)


def test_parse_documents_builds_documents() -> None:
    payload = [
        {"id": "a", "title": "A", "content": "alpha", "source": "s", "tags": ["x", "y"]},
        {"id": "b", "title": "B", "content": "beta"},
    ]
    docs = parse_documents(payload)
    assert docs[0] == Document(id="a", title="A", content="alpha", source="s", tags=("x", "y"))
    assert docs[1].source is None
    assert docs[1].tags == ()


def test_parse_documents_rejects_non_list() -> None:
    with pytest.raises(KnowledgeBaseError, match="JSON array"):
        parse_documents({"id": "a"})


def test_parse_documents_rejects_empty() -> None:
    with pytest.raises(KnowledgeBaseError, match="empty"):
        parse_documents([])


def test_parse_documents_requires_fields() -> None:
    with pytest.raises(KnowledgeBaseError, match="missing required field"):
        parse_documents([{"id": "a", "title": "A"}])


def test_parse_documents_rejects_non_object_item() -> None:
    with pytest.raises(KnowledgeBaseError, match="must be a JSON object"):
        parse_documents(["not-an-object"])


def test_parse_documents_rejects_string_tags() -> None:
    with pytest.raises(KnowledgeBaseError, match="'tags' must be a list"):
        parse_documents([{"id": "a", "title": "A", "content": "c", "tags": "nope"}])


def test_load_documents_missing_file(tmp_path: Path) -> None:
    with pytest.raises(KnowledgeBaseError, match="not found"):
        load_documents(tmp_path / "missing.json")


def test_load_documents_invalid_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{ not json", encoding="utf-8")
    with pytest.raises(KnowledgeBaseError, match="not valid JSON"):
        load_documents(bad)


def test_load_documents_roundtrip(tmp_path: Path) -> None:
    payload = [{"id": "a", "title": "A", "content": "alpha"}]
    file = tmp_path / "kb.json"
    file.write_text(json.dumps(payload), encoding="utf-8")
    docs = load_documents(file)
    assert docs == [Document(id="a", title="A", content="alpha")]
