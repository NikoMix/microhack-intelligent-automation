"""Provider strategy: build a configured OpenAI-compatible client per provider.

All three providers (GitHub Models, Azure OpenAI, Azure AI Foundry) speak the
OpenAI Chat Completions protocol, so we normalise on the ``openai`` SDK as a single
transport. This keeps the dependency surface tiny and works on the newest Python
runtimes where some Azure SDKs do not yet ship wheels.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from openai import AsyncAzureOpenAI, AsyncOpenAI, AzureOpenAI, OpenAI

from iauto_inference.errors import InferenceConfigError
from iauto_inference.settings import InferenceSettings, Provider

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Callable

_AAD_SCOPE = "https://cognitiveservices.azure.com/.default"


def _require(value: str | None, name: str, provider: Provider) -> str:
    if not value:
        raise InferenceConfigError(
            f"Provider '{provider.value}' requires {name}. "
            f"Set it in your environment or .env file."
        )
    return value


def _bearer_token_provider() -> Callable[[], str]:
    """Return a callable that yields a fresh Entra ID token.

    Imported lazily so the free GitHub Models path never needs ``azure-identity``.
    """
    try:
        # Lazy import: keeps the free GitHub Models path free of azure-identity.
        from azure.identity import (  # noqa: PLC0415
            DefaultAzureCredential,
            get_bearer_token_provider,
        )
    except ImportError as exc:  # pragma: no cover - exercised via integration only
        raise InferenceConfigError(
            "Entra ID auth requested but 'azure-identity' is not installed. "
            "Install the extra: pip install 'iauto-inference[azure]', or supply an API key."
        ) from exc
    return get_bearer_token_provider(DefaultAzureCredential(), _AAD_SCOPE)


def build_clients(settings: InferenceSettings) -> tuple[Any, Any]:
    """Build a ``(sync, async)`` OpenAI-compatible client pair for the active provider."""
    common: dict[str, Any] = {
        "timeout": settings.request_timeout,
        "max_retries": settings.max_retries,
    }

    if settings.provider is Provider.github:
        token = _require(settings.github_token, "GITHUB_TOKEN", Provider.github)
        base_url = settings.github_models_endpoint
        return (
            OpenAI(base_url=base_url, api_key=token, **common),
            AsyncOpenAI(base_url=base_url, api_key=token, **common),
        )

    if settings.provider is Provider.azure_openai:
        endpoint = _require(
            settings.azure_openai_endpoint, "AZURE_OPENAI_ENDPOINT", Provider.azure_openai
        )
        _require(
            settings.azure_openai_deployment, "AZURE_OPENAI_DEPLOYMENT", Provider.azure_openai
        )
        az_common: dict[str, Any] = {
            "azure_endpoint": endpoint,
            "api_version": settings.azure_openai_api_version,
            **common,
        }
        if settings.azure_openai_api_key:
            key = settings.azure_openai_api_key
            return (
                AzureOpenAI(api_key=key, **az_common),
                AsyncAzureOpenAI(api_key=key, **az_common),
            )
        provider = _bearer_token_provider()
        return (
            AzureOpenAI(azure_ad_token_provider=provider, **az_common),
            AsyncAzureOpenAI(azure_ad_token_provider=provider, **az_common),
        )

    # Azure AI Foundry via its OpenAI-compatible endpoint.
    endpoint = _require(settings.foundry_endpoint, "AZURE_AI_FOUNDRY_ENDPOINT", Provider.foundry)
    _require(settings.foundry_model, "AZURE_AI_FOUNDRY_MODEL", Provider.foundry)
    if settings.foundry_api_key:
        key = settings.foundry_api_key
        return (
            OpenAI(base_url=endpoint, api_key=key, **common),
            AsyncOpenAI(base_url=endpoint, api_key=key, **common),
        )
    # Entra ID: resolve a token now. For long-lived processes prefer an API key
    # or wire the token provider into a custom httpx auth flow.
    token = _bearer_token_provider()()
    return (
        OpenAI(base_url=endpoint, api_key=token, **common),
        AsyncOpenAI(base_url=endpoint, api_key=token, **common),
    )
