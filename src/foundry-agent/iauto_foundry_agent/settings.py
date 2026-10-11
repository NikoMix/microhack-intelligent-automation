"""Environment-driven configuration for the Foundry RAG lab."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

AgentRuntime = Literal["modular", "foundry"]


def _getenv(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _getint(name: str, default: int) -> int:
    raw = _getenv(name)
    return default if not raw else int(raw)


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    search_endpoint: str
    search_index: str = "iauto-foundry-kb"
    search_top_k: int = 4
    agent_runtime: AgentRuntime = "modular"
    app_insights_connection_string: str = ""
    foundry_project_endpoint: str = ""
    foundry_model: str = "gpt-4o-mini"

    @classmethod
    def from_env(cls) -> Settings:
        runtime = _getenv("IAUTO_AGENT_RUNTIME", "modular").lower()
        if runtime not in {"modular", "foundry"}:
            msg = "IAUTO_AGENT_RUNTIME must be 'modular' or 'foundry'."
            raise ValueError(msg)
        return cls(
            search_endpoint=_getenv("AZURE_SEARCH_ENDPOINT"),
            search_index=_getenv("AZURE_SEARCH_INDEX", "iauto-foundry-kb"),
            search_top_k=_getint("AZURE_SEARCH_TOP_K", 4),
            agent_runtime=runtime,  # type: ignore[arg-type]
            app_insights_connection_string=_getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"),
            foundry_project_endpoint=(
                _getenv("AZURE_AI_FOUNDRY_PROJECT_ENDPOINT")
                or _getenv("FOUNDRY_PROJECT_ENDPOINT")
                or _getenv("AZURE_AI_FOUNDRY_ENDPOINT")
            ),
            foundry_model=_getenv("AZURE_AI_FOUNDRY_MODEL")
            or _getenv("FOUNDRY_MODEL", "gpt-4o-mini"),
        )

    def require_search(self) -> None:
        """Validate that Azure AI Search configuration is present."""
        if not self.search_endpoint:
            msg = "Set AZURE_SEARCH_ENDPOINT to your Azure AI Search endpoint."
            raise ValueError(msg)
