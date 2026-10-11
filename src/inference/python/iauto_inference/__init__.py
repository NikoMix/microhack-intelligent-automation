"""Modular, provider-agnostic chat inference.

Single small surface that targets **GitHub Models** (free default), **Azure OpenAI**,
and **Azure AI Foundry** through one OpenAI-compatible transport. Swap providers with
an environment variable -- no code change.
"""

from __future__ import annotations

from iauto_inference.client import ChatMessage, ChatResult, InferenceClient
from iauto_inference.errors import InferenceConfigError, InferenceError
from iauto_inference.settings import InferenceSettings, Provider

__all__ = [
    "ChatMessage",
    "ChatResult",
    "InferenceClient",
    "InferenceConfigError",
    "InferenceError",
    "InferenceSettings",
    "Provider",
]

__version__ = "0.1.0"
