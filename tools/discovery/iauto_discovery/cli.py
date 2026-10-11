"""``iauto-discover`` — turn an automation inventory into a sizing/migration report."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from iauto_discovery import render
from iauto_discovery.engine import build_report
from iauto_discovery.loaders import load_inventory
from iauto_discovery.models import RoiAssumptions


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="iauto-discover",
        description=(
            "Assess a Power Platform automation inventory and recommend Azure targets, "
            "sizing, effort, security, and ROI (Module B.1.2)."
        ),
    )
    parser.add_argument("inventory", type=Path, help="Inventory file (.csv or .json).")
    parser.add_argument(
        "--assumptions",
        type=Path,
        default=None,
        help="Optional JSON file overriding the ROI economic assumptions.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write the report to this file instead of stdout.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of Markdown.",
    )
    parser.add_argument(
        "--narrative",
        action="store_true",
        help="Add an LLM executive narrative (needs the 'ai' extra + a provider).",
    )
    return parser


def _load_assumptions(path: Path | None) -> RoiAssumptions:
    if path is None:
        return RoiAssumptions()
    return RoiAssumptions.model_validate_json(path.read_text(encoding="utf-8"))


def _emit(text: str) -> None:
    """Write to stdout robustly, even on a non-UTF-8 console (e.g. Windows cp1252)."""
    data = text + "\n"
    try:
        sys.stdout.write(data)
    except UnicodeEncodeError:
        buffer = getattr(sys.stdout, "buffer", None)
        if buffer is not None:
            buffer.write(data.encode("utf-8", errors="replace"))
            buffer.flush()
        else:  # pragma: no cover - exotic stream with no buffer
            sys.stdout.write(data.encode("utf-8", errors="replace").decode("ascii", "replace"))


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code."""
    args = _build_parser().parse_args(argv)

    try:
        items = load_inventory(args.inventory)
    except (OSError, ValueError) as exc:
        print(f"error: failed to load inventory: {exc}", file=sys.stderr)
        return 2

    if not items:
        print("error: inventory is empty.", file=sys.stderr)
        return 2

    assumptions = _load_assumptions(args.assumptions)
    report = build_report(items, assumptions)

    if args.narrative:
        try:
            from iauto_discovery.narrative import generate_narrative  # noqa: PLC0415

            report.narrative = generate_narrative(report)
        except (RuntimeError, OSError) as exc:  # provider/config/network issues
            print(f"warning: narrative skipped: {exc}", file=sys.stderr)

    output = render.to_json(report) if args.json else render.to_markdown(report)

    if args.out is not None:
        args.out.write_text(output, encoding="utf-8")
        print(f"Wrote {args.out}", file=sys.stderr)
    else:
        _emit(output)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
