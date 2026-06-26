"""Knowledge-base documents: the corpus the agent grounds its answers on.

A :class:`Document` is the smallest retrievable unit (a passage / KB article). The local
fallback retriever indexes these in memory; the Azure AI Search retriever maps search
results back into the same shape, so feature code is identical across backends.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path
from typing import Any

from iauto_foundry_agent.errors import KnowledgeBaseError


@dataclass(frozen=True, slots=True)
class Document:
    """A single retrievable knowledge-base passage."""

    id: str
    title: str
    content: str
    source: str | None = None
    tags: tuple[str, ...] = field(default_factory=tuple)

    @property
    def searchable_text(self) -> str:
        """Title and content joined — the text a lexical retriever indexes."""
        return f"{self.title}\n{self.content}"


def default_knowledge_base_path() -> Path:
    """Return the path to the bundled sample knowledge base."""
    resource = files("iauto_foundry_agent").joinpath("data", "knowledge_base.json")
    return Path(str(resource))


def _coerce_document(raw: Any, *, index: int) -> Document:  # `raw` is a decoded JSON value
    if not isinstance(raw, dict):
        raise KnowledgeBaseError(
            f"Document #{index} must be a JSON object, got {type(raw).__name__}."
        )
    try:
        doc_id = str(raw["id"])
        title = str(raw["title"])
        content = str(raw["content"])
    except KeyError as exc:
        raise KnowledgeBaseError(
            f"Document #{index} is missing required field {exc.args[0]!r} "
            f"(expected 'id', 'title', 'content')."
        ) from exc

    source_raw = raw.get("source")
    source = str(source_raw) if source_raw is not None else None

    tags_raw = raw.get("tags", [])
    if not isinstance(tags_raw, Iterable) or isinstance(tags_raw, str):
        raise KnowledgeBaseError(f"Document #{index} 'tags' must be a list of strings.")
    tags = tuple(str(t) for t in tags_raw)

    return Document(id=doc_id, title=title, content=content, source=source, tags=tags)


def parse_documents(payload: Any) -> list[Document]:  # `payload` is a decoded JSON value
    """Validate and convert a decoded JSON payload into :class:`Document` objects."""
    if not isinstance(payload, list):
        raise KnowledgeBaseError(
            "Knowledge base must be a JSON array of documents at the top level."
        )
    if not payload:
        raise KnowledgeBaseError("Knowledge base is empty — add at least one document.")
    return [_coerce_document(item, index=i) for i, item in enumerate(payload)]


def load_documents(path: str | Path | None = None) -> list[Document]:
    """Load and validate a knowledge-base corpus from a JSON file.

    Args:
        path: Path to a JSON array of documents. When ``None`` the bundled sample KB
            is loaded.

    Raises:
        KnowledgeBaseError: if the file is missing, not valid JSON, or malformed.
    """
    resolved = Path(path) if path is not None else default_knowledge_base_path()
    try:
        text = resolved.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise KnowledgeBaseError(f"Knowledge base not found at '{resolved}'.") from exc
    except OSError as exc:  # pragma: no cover - filesystem edge case
        raise KnowledgeBaseError(f"Could not read knowledge base '{resolved}': {exc}") from exc

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise KnowledgeBaseError(f"Knowledge base '{resolved}' is not valid JSON: {exc}") from exc

    return parse_documents(payload)
