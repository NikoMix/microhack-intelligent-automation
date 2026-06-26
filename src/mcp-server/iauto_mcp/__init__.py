"""``iauto-mcp`` -- an intelligent-automation MCP server.

A small `Model Context Protocol <https://modelcontextprotocol.io>`_ server that exposes
provider-agnostic *intelligent automation* tools (document summarisation, migration-plan
drafting, discovery & sizing, and grounded RAG answers). Every AI-backed tool runs through
the shared :mod:`iauto_inference` layer, so it works on **GitHub Models** (free default),
**Azure OpenAI**, or **Azure AI Foundry** by configuration alone -- never by code change.

The public surface is intentionally tiny:

* :data:`iauto_mcp.server.mcp` -- the configured :class:`mcp.server.fastmcp.FastMCP` app.
* :func:`iauto_mcp.server.main` -- the stdio entry point (``iauto-mcp-server``).

Tool *logic* lives in :mod:`iauto_mcp.tools` as injectable coroutines that accept an
:class:`iauto_inference.InferenceClient`, which keeps them unit-testable with fakes and
free of any network or transport concerns.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0"
