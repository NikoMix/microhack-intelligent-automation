"""Sample knowledge-base ingestion for Azure AI Search."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Final

from azure.identity.aio import DefaultAzureCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchableField,
    SearchIndex,
    SimpleField,
)

from iauto_foundry_agent.settings import Settings
from iauto_foundry_agent.telemetry import start_span

KNOWLEDGE_PACKAGE: Final = "iauto_foundry_agent.knowledge"
KnowledgeFile = Path | Traversable


@dataclass(frozen=True, slots=True)
class KnowledgeChunk:
    """A section-level markdown chunk ready for Azure AI Search."""

    id: str
    title: str
    section: str
    content: str
    source_path: str
    chunk_id: str

    def as_document(self) -> dict[str, str]:
        return {
            "id": self.id,
            "title": self.title,
            "section": self.section,
            "content": self.content,
            "source_path": self.source_path,
            "chunk_id": self.chunk_id,
        }


def build_index(index_name: str) -> SearchIndex:
    """Build the compact keyword RAG index for the lab."""
    return SearchIndex(
        name=index_name,
        fields=[
            SimpleField(name="id", type="Edm.String", key=True, filterable=True),
            SearchableField(name="title", type="Edm.String", filterable=True),
            SearchableField(name="section", type="Edm.String", filterable=True),
            SearchableField(name="content", type="Edm.String"),
            SimpleField(name="source_path", type="Edm.String", filterable=True),
            SimpleField(name="chunk_id", type="Edm.String", filterable=True),
        ],
    )


def _chunk_id(source_name: str, section: str) -> str:
    digest = hashlib.sha256(f"{source_name}:{section}".encode()).hexdigest()
    return digest[:16]


def _normalise_section(line: str) -> str:
    return line.lstrip("#").strip() or "Overview"


def parse_markdown(source_name: str, markdown: str) -> list[KnowledgeChunk]:
    """Parse one markdown document into title/section chunks."""
    title = source_name.removesuffix(".md").replace("-", " ").title()
    current_section = "Overview"
    current_lines: list[str] = []
    chunks: list[KnowledgeChunk] = []

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if line.startswith("# "):
            title = _normalise_section(line)
            continue
        if line.startswith("## "):
            if current_lines:
                chunks.append(_make_chunk(source_name, title, current_section, current_lines))
            current_section = _normalise_section(line)
            current_lines = []
            continue
        if line:
            current_lines.append(line)

    if current_lines:
        chunks.append(_make_chunk(source_name, title, current_section, current_lines))
    return chunks


def _make_chunk(
    source_name: str,
    title: str,
    section: str,
    lines: list[str],
) -> KnowledgeChunk:
    chunk_id = _chunk_id(source_name, section)
    return KnowledgeChunk(
        id=chunk_id,
        title=title,
        section=section,
        content="\n".join(lines),
        source_path=f"knowledge/{source_name}",
        chunk_id=chunk_id,
    )


def load_sample_chunks(data_dir: Path | None = None) -> list[KnowledgeChunk]:
    """Load committed markdown samples from package resources or a caller-supplied directory."""
    if data_dir is not None:
        return _load_chunks_from_paths(sorted(data_dir.glob("*.md"), key=lambda path: path.name))
    package_files = resources.files(KNOWLEDGE_PACKAGE)
    paths = sorted(
        (path for path in package_files.iterdir() if path.name.endswith(".md")),
        key=lambda path: path.name,
    )
    return _load_chunks_from_paths(paths)


def _load_chunks_from_paths(paths: Iterable[KnowledgeFile]) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    for path in paths:
        chunks.extend(parse_markdown(path.name, path.read_text(encoding="utf-8")))
    return chunks


async def ingest_sample_knowledge(settings: Settings, data_dir: Path | None = None) -> int:
    """Create/update the Search index and upload committed sample KB chunks."""
    settings.require_search()
    chunks = load_sample_chunks(data_dir)
    documents = [chunk.as_document() for chunk in chunks]

    with start_span("search.ingest") as span:
        span.set_attribute("search.index", settings.search_index)
        span.set_attribute("search.documents", len(documents))
        credential = DefaultAzureCredential()
        index_client = SearchIndexClient(settings.search_endpoint, credential)
        search_client = SearchClient(settings.search_endpoint, settings.search_index, credential)
        try:
            await index_client.create_or_update_index(build_index(settings.search_index))
            if documents:
                await search_client.upload_documents(documents=documents)
        finally:
            await search_client.close()
            await index_client.close()
            await credential.close()
    return len(documents)
