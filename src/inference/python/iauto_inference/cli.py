"""``iauto-smoke`` -- a tiny CLI that proves the active provider works.

Used in Lab 0. Reads the environment, runs a one-line completion, and prints the
provider, model, and reply. Exit code 0 on success, 2 on configuration error.
"""

from __future__ import annotations

import argparse
import sys

from iauto_inference import InferenceClient
from iauto_inference.errors import InferenceConfigError, InferenceError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="iauto-smoke",
        description="Smoke-test the modular inference layer against the active provider.",
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default="In one short sentence, say hello and name the cloud you run on.",
        help="Prompt to send (optional).",
    )
    parser.add_argument("--model", default=None, help="Override the model/deployment id.")
    parser.add_argument(
        "--max-tokens", type=int, default=64, help="Cap the response length (default: 64)."
    )
    args = parser.parse_args(argv)

    try:
        client = InferenceClient.from_env()
        result = client.complete(args.prompt, model=args.model, max_tokens=args.max_tokens)
    except InferenceConfigError as exc:
        print(f"[config error] {exc}", file=sys.stderr)
        return 2
    except InferenceError as exc:
        print(f"[inference error] {exc}", file=sys.stderr)
        return 1

    print(f"provider : {result.provider}")
    print(f"model    : {result.model}")
    if result.completion_tokens is not None:
        print(f"tokens   : {result.prompt_tokens} prompt / {result.completion_tokens} completion")
    print(f"reply    : {result.text.strip()}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
