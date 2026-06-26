"""Tests for optional OpenTelemetry → Azure Monitor wiring."""

from __future__ import annotations

import builtins
import os
from collections.abc import Callable

import pytest
from iauto_foundry_agent import telemetry
from iauto_foundry_agent.errors import FoundryAgentError
from iauto_foundry_agent.settings import FoundryAgentSettings

_CONN = "InstrumentationKey=00000000-0000-0000-0000-000000000000"


def test_no_connection_string_is_noop() -> None:
    assert telemetry.configure_telemetry(settings=FoundryAgentSettings()) is False


def test_missing_extra_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "azure.monitor.opentelemetry":
            raise ImportError("not installed")
        return real_import(name, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(FoundryAgentError, match="telemetry"):
        telemetry.configure_telemetry(connection_string=_CONN)


def test_configures_azure_monitor_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("azure.monitor.opentelemetry")
    import azure.monitor.opentelemetry as azmon

    calls: list[str] = []

    def fake_configure(*, connection_string: str, **_kwargs: object) -> None:
        calls.append(connection_string)

    monkeypatch.setattr(azmon, "configure_azure_monitor", fake_configure)
    result = telemetry.configure_telemetry(
        connection_string=_CONN, service_name="svc", settings=FoundryAgentSettings()
    )
    assert result is True
    assert calls == [_CONN]


def test_service_name_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("azure.monitor.opentelemetry")
    import azure.monitor.opentelemetry as azmon

    monkeypatch.delenv("OTEL_SERVICE_NAME", raising=False)
    noop: Callable[..., None] = lambda **_kwargs: None  # noqa: E731
    monkeypatch.setattr(azmon, "configure_azure_monitor", noop)
    telemetry.configure_telemetry(connection_string=_CONN, service_name="my-service")
    assert os.environ.get("OTEL_SERVICE_NAME") == "my-service"
