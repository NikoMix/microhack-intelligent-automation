"""Configuration for the modular inference layer.

The same environment-variable contract is shared with the .NET twin (``IAuto.Inference``)
so labs can switch language without re-learning configuration.

Shared contract
---------------
``INFERENCE_PROVIDER``   github | azure_openai | foundry   (default: github)

GitHub Models (free, default):
    ``GITHUB_TOKEN``                personal access token / Actions token
    ``GITHUB_MODELS_ENDPOINT``      default https://models.github.ai/inference
    ``GITHUB_MODELS_MODEL``         default openai/gpt-4o-mini

Azure OpenAI:
    ``AZURE_OPENAI_ENDPOINT``       https://<resource>.openai.azure.com
    ``AZURE_OPENAI_API_KEY``        optional -- omit to use Entra ID (DefaultAzureCredential)
    ``AZURE_OPENAI_DEPLOYMENT``     deployment name (acts as the model id)
    ``AZURE_OPENAI_API_VERSION``    default 2024-10-21

Azure AI Foundry (OpenAI-compatible route):
    ``AZURE_AI_FOUNDRY_ENDPOINT``   e.g. https://<resource>.services.ai.azure.com/models
    ``AZURE_AI_FOUNDRY_MODEL``      model id, e.g. gpt-4o-mini
    ``AZURE_AI_FOUNDRY_API_KEY``    optional -- omit to use Entra ID
"""

from __future__ import annotations

from enum import Enum

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Provider(str, Enum):
    """Supported inference providers."""

    github = "github"
    azure_openai = "azure_openai"
    foundry = "foundry"


class InferenceSettings(BaseSettings):
    """Environment-driven settings. Read once and inject for testability."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    provider: Provider = Field(default=Provider.github, alias="INFERENCE_PROVIDER")

    # --- GitHub Models (free default) ---
    github_token: str | None = Field(default=None, alias="GITHUB_TOKEN")
    github_models_endpoint: str = Field(
        default="https://models.github.ai/inference", alias="GITHUB_MODELS_ENDPOINT"
    )
    github_models_model: str = Field(default="openai/gpt-4o-mini", alias="GITHUB_MODELS_MODEL")

    # --- Azure OpenAI ---
    azure_openai_endpoint: str | None = Field(default=None, alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str | None = Field(default=None, alias="AZURE_OPENAI_API_KEY")
    azure_openai_deployment: str | None = Field(default=None, alias="AZURE_OPENAI_DEPLOYMENT")
    azure_openai_api_version: str = Field(default="2024-10-21", alias="AZURE_OPENAI_API_VERSION")

    # --- Azure AI Foundry (OpenAI-compatible) ---
    foundry_endpoint: str | None = Field(default=None, alias="AZURE_AI_FOUNDRY_ENDPOINT")
    foundry_model: str | None = Field(default=None, alias="AZURE_AI_FOUNDRY_MODEL")
    foundry_api_key: str | None = Field(default=None, alias="AZURE_AI_FOUNDRY_API_KEY")

    # --- transport tuning ---
    request_timeout: float = Field(default=60.0, alias="INFERENCE_TIMEOUT")
    max_retries: int = Field(default=3, alias="INFERENCE_MAX_RETRIES")

    def default_model(self) -> str | None:
        """Return the configured default model/deployment id for the active provider."""
        if self.provider is Provider.github:
            return self.github_models_model
        if self.provider is Provider.azure_openai:
            return self.azure_openai_deployment
        return self.foundry_model
