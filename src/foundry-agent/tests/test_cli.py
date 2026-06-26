"""Tests for the command-line interface (no provider, no network)."""

from __future__ import annotations

import pytest
from iauto_foundry_agent import cli
from iauto_foundry_agent.errors import FoundryAgentError


def test_list_prints_knowledge_base(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main(["--list"])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "Knowledge base:" in out
    assert "kb-001" in out


def test_show_context_prints_passages(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main(["--show-context", "how do I connect to the vpn"])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "[1]" in out
    assert "GlobalProtect" in out


def test_show_context_requires_query(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main(["--show-context"])
    err = capsys.readouterr().err
    assert exit_code == 2
    assert "requires a query" in err


def test_show_context_no_match(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main(["--show-context", "zzzquux nonexistentterm"])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "No matching passages" in out


def test_no_question_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main([])
    err = capsys.readouterr().err
    assert exit_code == 2
    assert "usage:" in err.lower()


def test_backend_override_unknown_choice_exits() -> None:
    with pytest.raises(SystemExit):
        cli.main(["--backend", "not-a-backend", "question?"])


def test_ask_success(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    class FakeAgent:
        @classmethod
        def from_env(cls, **_kwargs: object) -> FakeAgent:
            return cls()

        async def ask(self, _question: str) -> str:
            return "  Use GlobalProtect. [1]  "

    monkeypatch.setattr(cli, "GroundedKnowledgeAgent", FakeAgent)
    exit_code = cli.main(["How do I connect to the VPN?"])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert out.strip() == "Use GlobalProtect. [1]"


def test_ask_config_error_returns_2(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    class BrokenAgent:
        @classmethod
        def from_env(cls, **_kwargs: object) -> BrokenAgent:
            raise FoundryAgentError("no provider configured")

    monkeypatch.setattr(cli, "GroundedKnowledgeAgent", BrokenAgent)
    exit_code = cli.main(["a question"])
    err = capsys.readouterr().err
    assert exit_code == 2
    assert "config error" in err
