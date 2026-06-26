"""Optional OpenTelemetry tracing for the MCP server -- off by default and stdout-safe.

The MCP **stdio** transport owns ``stdout`` for the JSON-RPC stream, so telemetry must never
write there. When ``IAUTO_OTEL_ENABLED`` is truthy, spans are exported to ``stderr`` via the
console exporter. For production, point ``OTEL_EXPORTER_OTLP_ENDPOINT`` at Azure Monitor /
Application Insights and swap in the OTLP exporter (see the Lab 5 README upgrade notes).

Spans are always created through :func:`traced`; until :func:`setup_telemetry` installs a
provider they are cheap no-ops, so feature code can stay telemetry-agnostic.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

_TRACER = trace.get_tracer("iauto_mcp")
_TRUTHY = frozenset({"1", "true", "yes", "on"})


def telemetry_enabled() -> bool:
    """Return ``True`` when ``IAUTO_OTEL_ENABLED`` opts telemetry in."""
    return os.getenv("IAUTO_OTEL_ENABLED", "").strip().lower() in _TRUTHY


def setup_telemetry(service_name: str = "iauto-mcp-server") -> bool:
    """Install a ``stderr`` span exporter when enabled; return whether tracing is active."""
    if not telemetry_enabled():
        return False
    if not isinstance(trace.get_tracer_provider(), TracerProvider):
        provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter(out=sys.stderr)))
        trace.set_tracer_provider(provider)
    return True


@contextmanager
def traced(name: str, **attributes: str | int | float | bool) -> Iterator[None]:
    """Execute a block inside a span (a no-op until :func:`setup_telemetry` runs)."""
    with _TRACER.start_as_current_span(name) as span:
        for key, value in attributes.items():
            span.set_attribute(key, value)
        yield
