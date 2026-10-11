"""OpenTelemetry setup for Azure Monitor and local spans."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.trace import Span

_CONFIGURED = False


def configure_telemetry(connection_string: str) -> None:
    """Configure Azure Monitor OpenTelemetry when a connection string is supplied."""
    global _CONFIGURED  # noqa: PLW0603
    if not connection_string or _CONFIGURED:
        return
    configure_azure_monitor(connection_string=connection_string)
    _CONFIGURED = True


def tracer_name() -> str:
    return "iauto_foundry_agent"


@contextmanager
def start_span(name: str) -> Iterator[Span]:
    """Start a named span using the package tracer."""
    tracer = trace.get_tracer(tracer_name())
    with tracer.start_as_current_span(name) as span:
        yield span
