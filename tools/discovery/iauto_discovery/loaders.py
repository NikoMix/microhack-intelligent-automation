"""Load an automation inventory from CSV or JSON into validated models."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from iauto_discovery.models import InventoryItem

_ITEMS_ADAPTER = TypeAdapter(list[InventoryItem])
_TRUE = {"true", "1", "yes", "y"}
_FALSE = {"false", "0", "no", "n", ""}


def _coerce_bool(value: str) -> bool:
    token = value.strip().lower()
    if token in _TRUE:
        return True
    if token in _FALSE:
        return False
    msg = f"Cannot interpret {value!r} as a boolean."
    raise ValueError(msg)


def _coerce_row(row: dict[str, str]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, raw in row.items():
        if key is None:
            continue
        field = key.strip()
        value = (raw or "").strip()
        if field in ("on_prem_dependency", "premium_licensed"):
            cleaned[field] = _coerce_bool(value)
        elif field in ("runs_per_day", "avg_minutes", "connectors"):
            cleaned[field] = value or 0
        else:
            cleaned[field] = value
    return cleaned


def load_inventory(path: str | Path) -> list[InventoryItem]:
    """Load and validate an inventory from a ``.csv`` or ``.json`` file."""
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "items" in data:
            data = data["items"]
        return _ITEMS_ADAPTER.validate_python(data)

    if suffix == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            rows = [_coerce_row(row) for row in csv.DictReader(handle)]
        return _ITEMS_ADAPTER.validate_python(rows)

    msg = f"Unsupported inventory format {suffix!r}; use .csv or .json."
    raise ValueError(msg)
