"""Tests for the ``iauto-discover`` CLI entry point."""

from __future__ import annotations

import json
from pathlib import Path

from iauto_discovery.cli import main

_CSV = """name,automation_type,runs_per_day,avg_minutes,premium_licensed
Lead routing,cloud_flow,120,1,true
Invoice bot,ai_builder_doc,40,3,true
"""


def _write_inv(tmp_path: Path) -> Path:
    path = tmp_path / "inv.csv"
    path.write_text(_CSV, encoding="utf-8")
    return path


def test_cli_markdown_to_file(tmp_path: Path) -> None:
    inv = _write_inv(tmp_path)
    out = tmp_path / "report.md"
    code = main([str(inv), "--out", str(out)])
    assert code == 0
    assert out.exists()
    assert "# Discovery & sizing report" in out.read_text(encoding="utf-8")


def test_cli_json_to_file(tmp_path: Path) -> None:
    inv = _write_inv(tmp_path)
    out = tmp_path / "report.json"
    code = main([str(inv), "--json", "--out", str(out)])
    assert code == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["summary"]["total_items"] == 2


def test_cli_stdout(capsys, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    inv = _write_inv(tmp_path)
    code = main([str(inv)])
    assert code == 0
    assert "Discovery & sizing report" in capsys.readouterr().out


def test_cli_missing_file_returns_2(tmp_path: Path) -> None:
    code = main([str(tmp_path / "nope.csv")])
    assert code == 2


def test_cli_empty_inventory_returns_2(tmp_path: Path) -> None:
    path = tmp_path / "empty.csv"
    path.write_text("name,automation_type\n", encoding="utf-8")
    code = main([str(path)])
    assert code == 2
