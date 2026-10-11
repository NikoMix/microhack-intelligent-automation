"""Tests for environment-driven settings and provider selection."""

from __future__ import annotations

import pytest
from iauto_inference import InferenceConfigError, InferenceSettings, Provider
from iauto_inference.providers import build_clients


def test_defaults_to_github_provider() -> None:
    settings = InferenceSettings()
    assert settings.provider is Provider.github
    assert settings.github_models_endpoint == "https://models.github.ai/inference"
    assert settings.default_model() == "openai/gpt-4o-mini"


def test_reads_provider_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INFERENCE_PROVIDER", "azure_openai")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    settings = InferenceSettings()
    assert settings.provider is Provider.azure_openai
    assert settings.default_model() == "gpt-4o-mini"


def test_github_requires_token() -> None:
    settings = InferenceSettings(provider=Provider.github, github_token=None)
    with pytest.raises(InferenceConfigError, match="GITHUB_TOKEN"):
        build_clients(settings)


def test_azure_openai_requires_endpoint_and_deployment() -> None:
    settings = InferenceSettings(provider=Provider.azure_openai)
    with pytest.raises(InferenceConfigError, match="AZURE_OPENAI_ENDPOINT"):
        build_clients(settings)


def test_foundry_requires_endpoint_and_model() -> None:
    settings = InferenceSettings(provider=Provider.foundry, foundry_endpoint=None)
    with pytest.raises(InferenceConfigError, match="AZURE_AI_FOUNDRY_ENDPOINT"):
        build_clients(settings)


def test_github_client_builds_with_token() -> None:
    settings = InferenceSettings(provider=Provider.github, github_token="ghp_fake")  # noqa: S106
    sync_client, async_client = build_clients(settings)
    assert str(sync_client.base_url).rstrip("/").endswith("models.github.ai/inference")
    assert async_client is not None
