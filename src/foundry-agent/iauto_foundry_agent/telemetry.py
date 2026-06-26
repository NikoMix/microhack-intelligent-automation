"""Optional OpenTelemetry → Azure Monitor / Application Insights wiring.

Telemetry is *opt-in* and lazily loaded: with no connection string this is a no-op, so the
free local lab needs neither the ``telemetry`` extra nor any Azure resource. When
``APPLICATIONINSIGHTS_CONNECTION_STRING`` is set, traces and metrics (including the agent's
model calls) flow to Application Insights.

> The Bicep in ``infra/bicep/foundry-search`` provisions the Application Insights resource and
> surfaces its connection string.
"""

from __future__ import annotations

import os

from iauto_foundry_agent.errors import FoundryAgentError
from iauto_foundry_agent.settings import FoundryAgentSettings


def configure_telemetry(
    *,
    connection_string: str | None = None,
    service_name: str | None = None,
    settings: FoundryAgentSettings | None = None,
) -> bool:
    """Configure Azure Monitor OpenTelemetry if a connection string is available.

    Resolution order for the connection string: explicit argument → ``settings`` →
    ``APPLICATIONINSIGHTS_CONNECTION_STRING`` environment variable.

    Returns:
        ``True`` if telemetry was configured, ``False`` if no connection string was found
        (a deliberate no-op for the offline / free path).

    Raises:
        FoundryAgentError: if a connection string is present but the optional ``telemetry``
            extra is not installed.
    """
    resolved_settings = settings or FoundryAgentSettings()
    resolved_cs = (
        connection_string
        or resolved_settings.applicationinsights_connection_string
        or os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
    )
    if not resolved_cs:
        return False

    resolved_service = service_name or resolved_settings.otel_service_name
    # configure_azure_monitor reads OTEL_SERVICE_NAME for the resource service.name.
    os.environ.setdefault("OTEL_SERVICE_NAME", resolved_service)

    try:
        from azure.monitor.opentelemetry import (  # noqa: PLC0415 - optional 'telemetry' extra
            configure_azure_monitor,
        )
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise FoundryAgentError(
            "Telemetry requires the 'telemetry' extra: "
            "pip install 'iauto-foundry-agent[telemetry]'."
        ) from exc

    configure_azure_monitor(connection_string=resolved_cs)
    return True
