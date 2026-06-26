"""Tests for inventory loading (CSV + JSON) and validation."""

from __future__ import annotations

from pathlib import Path

import pytest
from iauto_discovery.loaders import load_inventory
from iauto_discovery.models import AutomationType

_CSV = """name,automation_type,runs_per_day,avg_minutes,connectors,complexity,data_sensitivity,on_prem_dependency,premium_licensed
Invoice bot,ai_builder_doc,40,3,4,medium,high,true,yes
Lead routing,cloud_flow,120,1,3,low,low,no,0
"""

_JSON = """{"items": [
  {"name": "Nightly sync", "automation_type": "unattended_rpa", "runs_per_day": 1, "avg_minutes": 90}
]}"""


def test_load_csv(tmp_path: Path) -> None:
    path = tmp_path / "inv.csv"
    path.write_text(_CSV, encoding="utf-8")
    items = load_inventory(path)
    assert len(items) == 2
    assert items[0].automation_type is AutomationType.AI_BUILDER_DOC
    assert items[0].on_prem_dependency is True
    assert items[0].premium_licensed is True
    assert items[1].on_prem_dependency is False
    assert items[1].premium_licensed is False


def test_load_json_with_items_wrapper(tmp_path: Path) -> None:
    path = tmp_path / "inv.json"
    path.write_text(_JSON, encoding="utf-8")
    items = load_inventory(path)
    assert len(items) == 1
    assert items[0].automation_type is AutomationType.UNATTENDED_RPA


def test_load_json_bare_array(tmp_path: Path) -> None:
    path = tmp_path / "inv.json"
    path.write_text('[{"name": "x", "automation_type": "cloud_flow"}]', encoding="utf-8")
    items = load_inventory(path)
    assert len(items) == 1


def test_unsupported_suffix(tmp_path: Path) -> None:
    path = tmp_path / "inv.xml"
    path.write_text("<nope/>", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported inventory format"):
        load_inventory(path)


def test_bad_boolean_rejected(tmp_path: Path) -> None:
    path = tmp_path / "inv.csv"
    path.write_text(
        "name,automation_type,on_prem_dependency\nx,cloud_flow,maybe\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="boolean"):
        load_inventory(path)
