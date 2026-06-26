"""Configuration for the Foundry agent and its RAG retriever.

Reuses the shared modular-inference contract for provider selection (``INFERENCE_PROVIDER``
and friends, owned by :mod:`iauto_inference`) and adds the agent / retrieval knobs on top.
Switching from the local fallback index to Azure AI Search is a configuration change
(``RETRIEVER_BACKEND``), never a code change — the same philosophy as the inference layer.

Retriever contract
------------------
``RETRIEVER_BACKEND``   local | azure_search   (default: local — runs with zero Azure)

Local fallback (default):
    ``KNOWLEDGE_BASE_PATH``   path to a JSON corpus; omit to use the bundled sample KB.
    ``RETRIEVAL_TOP_K``       number of passages to return (default: 4).

Azure AI Search (upgrade):
    ``AZURE_SEARCH_ENDPOINT``   https://<service>.search.windows.net
    ``AZURE_SEARCH_INDEX``      index name (default: knowledge-index)
    ``AZURE_SEARCH_API_KEY``    optional — omit to use Entra ID (DefaultAzureCredential)
    ``AZURE_SEARCH_*_FIELD``    map index fields to id/title/content/source.

Agent / telemetry:
    ``AGENT_NAME`` / ``AGENT_INSTRUCTIONS``   identity + optional system-prompt override.
    ``APPLICATIONINSIGHTS_CONNECTION_STRING`` enables OpenTelemetry → Azure Monitor.
    ``OTEL_SERVICE_NAME``                      service name reported in traces.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from iauto_foundry_agent.documents import default_knowledge_base_path


class RetrieverBackend(StrEnum):
    """Supported retrieval backends."""

    local = "local"
    azure_search = "azure_search"


class FoundryAgentSettings(BaseSettings):
    """Environment-driven settings. Read once and inject for testability."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    retriever_backend: RetrieverBackend = Field(
        default=RetrieverBackend.local, alias="RETRIEVER_BACKEND"
    )

    # --- local fallback index ---
    knowledge_base_path: str | None = Field(default=None, alias="KNOWLEDGE_BASE_PATH")
    retrieval_top_k: int = Field(default=4, ge=1, le=50, alias="RETRIEVAL_TOP_K")

    # --- agent identity ---
    agent_name: str = Field(default="kb-assistant", alias="AGENT_NAME")
    agent_instructions: str | None = Field(default=None, alias="AGENT_INSTRUCTIONS")

    # --- Azure AI Search (upgrade path) ---
    azure_search_endpoint: str | None = Field(default=None, alias="AZURE_SEARCH_ENDPOINT")
    azure_search_index: str = Field(default="knowledge-index", alias="AZURE_SEARCH_INDEX")
    azure_search_api_key: str | None = Field(default=None, alias="AZURE_SEARCH_API_KEY")
    azure_search_id_field: str = Field(default="id", alias="AZURE_SEARCH_ID_FIELD")
    azure_search_title_field: str = Field(default="title", alias="AZURE_SEARCH_TITLE_FIELD")
    azure_search_content_field: str = Field(default="content", alias="AZURE_SEARCH_CONTENT_FIELD")
    azure_search_source_field: str = Field(default="source", alias="AZURE_SEARCH_SOURCE_FIELD")

    # --- telemetry ---
    applicationinsights_connection_string: str | None = Field(
        default=None, alias="APPLICATIONINSIGHTS_CONNECTION_STRING"
    )
    otel_service_name: str = Field(default="iauto-foundry-agent", alias="OTEL_SERVICE_NAME")

    def resolved_knowledge_base_path(self) -> Path:
        """Return the configured KB path, or the bundled sample when unset."""
        if self.knowledge_base_path:
            return Path(self.knowledge_base_path)
        return default_knowledge_base_path()
