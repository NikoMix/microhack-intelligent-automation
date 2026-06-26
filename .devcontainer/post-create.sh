#!/usr/bin/env bash
# Dev container post-create: install the tools the labs need that aren't covered
# by dev container features. Idempotent and license-free.
set -euo pipefail

echo "==> Installing uv (Python package/venv manager)…"
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

echo "==> Installing Azure Functions Core Tools v4…"
if ! command -v func >/dev/null 2>&1; then
  npm install -g azure-functions-core-tools@4 --unsafe-perm true
fi

echo "==> Installing Bicep CLI via az…"
az bicep install || true

echo "==> Restoring Python inference env (3.12)…"
if [ -d src/inference/python ]; then
  (cd src/inference/python && uv venv --python 3.12 && uv pip install -e ".[dev,azure,telemetry]") || true
fi

echo "==> Restoring .NET solution…"
if [ -f src/inference/dotnet/IAuto.Inference.slnx ]; then
  dotnet restore src/inference/dotnet/IAuto.Inference.slnx || true
fi

echo "==> Done. Default inference provider: GitHub Models (set GITHUB_TOKEN to use it)."
