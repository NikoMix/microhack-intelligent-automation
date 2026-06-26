"""Azure AI Search retriever — the production RAG upgrade.

Implements the same :class:`~iauto_foundry_agent.retrieval.base.Retriever` protocol as the
local BM25 index, so swapping ``RETRIEVER_BACKEND=azure_search`` requires no feature-code
change. Authentication prefers **Entra ID** via ``DefaultAzureCredential``; an API key is a
class-delivery fallback. Azure SDKs are imported lazily so the free local path needs none of
them installed.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING, Any, Protocol

from iauto_foundry_agent.documents import Document
from iauto_foundry_agent.errors import RetrieverError
from iauto_foundry_agent.retrieval.base import SearchHit

if TYPE_CHECKING:  # pragma: no cover - typing only
    from iauto_foundry_agent.settings import FoundryAgentSettings

_SCORE_FIELD = "@search.score"


class SupportsSearch(Protocol):
    """Structural type for an Azure AI Search client (the subset we call)."""

    def search(self, search_text: str, *, top: int) -> Iterable[Mapping[str, Any]]:
        """Run a search and yield result documents (dict-like rows)."""
        ...


class AzureAISearchRetriever:
    """Retrieve passages from an Azure AI Search index.

    Args:
        search_client: a configured Azure ``SearchClient`` (or any object implementing
            :class:`SupportsSearch` — handy for tests).
        id_field/title_field/content_field/source_field: index field names mapped onto
            :class:`~iauto_foundry_agent.documents.Document`.
    """

    def __init__(
        self,
        search_client: SupportsSearch,
        *,
        id_field: str = "id",
        title_field: str = "title",
        content_field: str = "content",
        source_field: str = "source",
    ) -> None:
        self._client = search_client
        self._id_field = id_field
        self._title_field = title_field
        self._content_field = content_field
        self._source_field = source_field

    def _to_hit(self, row: Mapping[str, Any]) -> SearchHit:
        source_value = row.get(self._source_field)
        document = Document(
            id=str(row.get(self._id_field, "")),
            title=str(row.get(self._title_field, "")),
            content=str(row.get(self._content_field, "")),
            source=str(source_value) if source_value is not None else None,
        )
        score = float(row.get(_SCORE_FIELD, 0.0))
        return SearchHit(document=document, score=score)

    def search(self, query: str, *, top_k: int = 4) -> list[SearchHit]:
        """Return up to ``top_k`` documents most relevant to ``query``."""
        if top_k <= 0:
            return []
        try:
            rows = self._client.search(query, top=top_k)
            return [self._to_hit(row) for row in rows]
        except RetrieverError:
            raise
        except Exception as exc:  # normalise any Azure SDK error into our hierarchy
            raise RetrieverError(f"Azure AI Search query failed: {exc}") from exc

    @classmethod
    def from_settings(cls, settings: FoundryAgentSettings) -> AzureAISearchRetriever:
        """Build a retriever from settings, resolving Entra ID or key auth."""
        if not settings.azure_search_endpoint:
            raise RetrieverError(
                "AZURE_SEARCH_ENDPOINT is required for the 'azure_search' backend. "
                "Set it (and AZURE_SEARCH_INDEX), or use RETRIEVER_BACKEND=local."
            )
        client = _build_search_client(settings)
        return cls(
            client,
            id_field=settings.azure_search_id_field,
            title_field=settings.azure_search_title_field,
            content_field=settings.azure_search_content_field,
            source_field=settings.azure_search_source_field,
        )


def _build_search_client(settings: FoundryAgentSettings) -> SupportsSearch:
    """Construct an Azure ``SearchClient`` with Entra ID (preferred) or key auth."""
    try:
        from azure.core.credentials import AzureKeyCredential  # noqa: PLC0415 - optional extra
        from azure.search.documents import SearchClient  # noqa: PLC0415 - optional extra
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise RetrieverError(
            "Azure AI Search support requires the 'azure' extra: "
            "pip install 'iauto-foundry-agent[azure]'."
        ) from exc

    endpoint = settings.azure_search_endpoint
    if endpoint is None:  # pragma: no cover - guarded by from_settings
        raise RetrieverError("AZURE_SEARCH_ENDPOINT is required for the 'azure_search' backend.")

    credential: Any
    if settings.azure_search_api_key:
        credential = AzureKeyCredential(settings.azure_search_api_key)
    else:
        try:
            from azure.identity import DefaultAzureCredential  # noqa: PLC0415 - optional extra
        except ImportError as exc:  # pragma: no cover
            raise RetrieverError(
                "Entra ID auth requires 'azure-identity' (bundled with the 'azure' extra)."
            ) from exc
        credential = DefaultAzureCredential()

    client: SupportsSearch = SearchClient(
        endpoint=endpoint,
        index_name=settings.azure_search_index,
        credential=credential,
    )
    return client
