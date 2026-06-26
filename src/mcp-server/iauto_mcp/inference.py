"""Lazy, process-wide construction of the shared :class:`~iauto_inference.InferenceClient`.

Construction is deferred until the first tool call so the MCP server can start without
credentials; a missing or inconsistent provider configuration then surfaces as a clear
:class:`iauto_inference.InferenceConfigError` *at call time* rather than at startup.

Tests never call this -- they inject a fake-backed client straight into the
:mod:`iauto_mcp.tools` coroutines, keeping the suite network-free.
"""

from __future__ import annotations

from functools import lru_cache

from iauto_inference import InferenceClient


@lru_cache(maxsize=1)
def get_client() -> InferenceClient:
    """Return a memoised :class:`InferenceClient` built from the environment/``.env``."""
    return InferenceClient.from_env()
