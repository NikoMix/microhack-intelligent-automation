"""Provision and load the Azure AI Search index for the RAG upgrade.

This is the *authoring* counterpart to :mod:`iauto_foundry_agent.retrieval.azure_search` (which
only reads). It creates an index whose field names match the retriever's configuration and uploads
the knowledge-base corpus, so the Azure step is one reproducible command — ``iauto-foundry-index``
— instead of a copy-pasted snippet that can drift from the code.

Authentication prefers **Entra ID** via ``DefaultAzureCredential``; an API key is a class-delivery
fallback. Azure SDKs are imported lazily so the free local path needs none of them installed.
"""

from __future__ import annotations

import argparse
import contextlib
import sys
from collections.abc import Sequence
from typing import Any, Protocol

from iauto_foundry_agent.documents import Document, load_documents
from iauto_foundry_agent.errors import FoundryAgentError, RetrieverError
from iauto_foundry_agent.settings import FoundryAgentSettings

_TAGS_FIELD = "tags"


class SupportsIndexAdmin(Protocol):
    """Structural type for an Azure ``SearchIndexClient`` (the subset we call)."""

    def create_or_update_index(self, index: Any) -> Any:
        """Create or update a search index definition."""
        ...

    def delete_index(self, index: Any) -> None:
        """Delete a search index by name or definition."""
        ...


class SupportsDocumentUpload(Protocol):
    """Structural type for an Azure ``SearchClient`` upload surface."""

    def upload_documents(self, documents: Any) -> Any:
        """Upload (merge-or-upload) documents into the index."""
        ...


def build_documents_payload(
    settings: FoundryAgentSettings, documents: Sequence[Document]
) -> list[dict[str, Any]]:
    """Map :class:`Document` objects onto index rows using the configured field names.

    Pure and offline — the keys mirror exactly what
    :class:`~iauto_foundry_agent.retrieval.azure_search.AzureAISearchRetriever` reads back.
    """
    return [
        {
            settings.azure_search_id_field: doc.id,
            settings.azure_search_title_field: doc.title,
            settings.azure_search_content_field: doc.content,
            settings.azure_search_source_field: doc.source or "",
            _TAGS_FIELD: list(doc.tags),
        }
        for doc in documents
    ]


def _require_endpoint(settings: FoundryAgentSettings) -> str:
    endpoint = settings.azure_search_endpoint
    if not endpoint:
        raise RetrieverError(
            "AZURE_SEARCH_ENDPOINT is required to provision the index. "
            "Set it (and AZURE_SEARCH_INDEX) from the Bicep outputs."
        )
    return endpoint


def _build_credential(settings: FoundryAgentSettings) -> Any:
    """Resolve Entra ID (preferred) or API-key credentials for Azure AI Search."""
    if settings.azure_search_api_key:
        from azure.core.credentials import AzureKeyCredential  # noqa: PLC0415 - optional extra

        return AzureKeyCredential(settings.azure_search_api_key)
    try:
        from azure.identity import DefaultAzureCredential  # noqa: PLC0415 - optional extra
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise RetrieverError(
            "Entra ID auth requires 'azure-identity' (bundled with the 'azure' extra)."
        ) from exc
    return DefaultAzureCredential()


def _build_index_definition(settings: FoundryAgentSettings) -> Any:
    """Construct an Azure ``SearchIndex`` whose fields match the retriever's mapping."""
    try:
        from azure.search.documents.indexes.models import (  # noqa: PLC0415 - optional extra
            SearchableField,
            SearchFieldDataType,
            SearchIndex,
            SimpleField,
        )
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise RetrieverError(
            "Azure AI Search support requires the 'azure' extra: "
            "pip install 'iauto-foundry-agent[azure]'."
        ) from exc

    fields = [
        SimpleField(name=settings.azure_search_id_field, type=SearchFieldDataType.String, key=True),
        SearchableField(name=settings.azure_search_title_field, type=SearchFieldDataType.String),
        SearchableField(name=settings.azure_search_content_field, type=SearchFieldDataType.String),
        SimpleField(
            name=settings.azure_search_source_field,
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SimpleField(
            name=_TAGS_FIELD,
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            filterable=True,
            facetable=True,
        ),
    ]
    return SearchIndex(name=settings.azure_search_index, fields=fields)


def _build_index_client(settings: FoundryAgentSettings) -> SupportsIndexAdmin:
    try:
        from azure.search.documents.indexes import SearchIndexClient  # noqa: PLC0415 - optional
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise RetrieverError(
            "Azure AI Search support requires the 'azure' extra: "
            "pip install 'iauto-foundry-agent[azure]'."
        ) from exc
    client: SupportsIndexAdmin = SearchIndexClient(
        endpoint=_require_endpoint(settings), credential=_build_credential(settings)
    )
    return client


def _build_upload_client(settings: FoundryAgentSettings) -> SupportsDocumentUpload:
    try:
        from azure.search.documents import SearchClient  # noqa: PLC0415 - optional extra
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise RetrieverError(
            "Azure AI Search support requires the 'azure' extra: "
            "pip install 'iauto-foundry-agent[azure]'."
        ) from exc
    client: SupportsDocumentUpload = SearchClient(
        endpoint=_require_endpoint(settings),
        index_name=settings.azure_search_index,
        credential=_build_credential(settings),
    )
    return client


def provision_index(
    settings: FoundryAgentSettings,
    *,
    documents: Sequence[Document] | None = None,
    recreate: bool = False,
    index_client: SupportsIndexAdmin | None = None,
    search_client: SupportsDocumentUpload | None = None,
) -> int:
    """Create/update the Azure AI Search index and upload the knowledge base.

    Args:
        settings: agent settings carrying the Search endpoint, index name and field mapping.
        documents: corpus to upload; defaults to the configured (or bundled) knowledge base.
        recreate: when ``True``, delete the index first for a clean rebuild.
        index_client/search_client: inject clients for testing; built from settings when omitted.

    Returns:
        The number of documents uploaded.
    """
    _require_endpoint(settings)
    corpus = (
        list(documents)
        if documents is not None
        else load_documents(settings.resolved_knowledge_base_path())
    )

    admin = index_client if index_client is not None else _build_index_client(settings)
    if recreate:
        # Best-effort: the index may not exist yet on a first run.
        with contextlib.suppress(Exception):
            admin.delete_index(settings.azure_search_index)

    try:
        admin.create_or_update_index(_build_index_definition(settings))
    except RetrieverError:
        raise
    except Exception as exc:  # normalise Azure SDK errors into our hierarchy
        raise RetrieverError(f"Could not create the Azure AI Search index: {exc}") from exc

    uploader = search_client if search_client is not None else _build_upload_client(settings)
    payload = build_documents_payload(settings, corpus)
    try:
        uploader.upload_documents(payload)
    except Exception as exc:  # normalise Azure SDK errors into our hierarchy
        raise RetrieverError(f"Could not upload documents to Azure AI Search: {exc}") from exc
    return len(payload)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="iauto-foundry-index",
        description="Create the Azure AI Search index and load the knowledge base (RAG upgrade).",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete and recreate the index for a clean rebuild.",
    )
    parser.add_argument(
        "--knowledge-base",
        default=None,
        metavar="PATH",
        help="Path to a JSON corpus to load (defaults to the bundled sample KB).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for index provisioning. Returns a process exit code."""
    args = _build_parser().parse_args(argv)
    settings = FoundryAgentSettings()
    documents = load_documents(args.knowledge_base) if args.knowledge_base else None
    try:
        count = provision_index(settings, documents=documents, recreate=args.recreate)
    except FoundryAgentError as exc:
        print(f"[config error] {exc}", file=sys.stderr)
        return 2
    print(
        f"Provisioned index '{settings.azure_search_index}' at {settings.azure_search_endpoint} "
        f"with {count} documents."
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
