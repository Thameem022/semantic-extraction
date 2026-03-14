#!/usr/bin/env bash
# Run unit tests using the project venv. From repo root: ./scripts/run-tests.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

VENV_PYTHON=""
if [[ -x "${PROJECT_ROOT}/.venv/bin/python" ]]; then
  VENV_PYTHON="${PROJECT_ROOT}/.venv/bin/python"
elif [[ -x "${PROJECT_ROOT}/venv/bin/python" ]]; then
  VENV_PYTHON="${PROJECT_ROOT}/venv/bin/python"
fi

if [[ -z "${VENV_PYTHON}" ]]; then
  echo "No .venv or venv found. Create one and install dev deps:"
  echo "  python3 -m venv .venv"
  echo "  .venv/bin/pip install -r requirements-dev.txt"
  echo "  ./scripts/run-tests.sh"
  exit 1
fi

# Install dev deps (pytest, etc.) if not present
if ! "${VENV_PYTHON}" -c "import pytest" 2>/dev/null; then
  echo "Installing dev dependencies (pytest, etc.)..."
  "${VENV_PYTHON}" -m pip install -q -r requirements-dev.txt
fi

"${VENV_PYTHON}" -m pytest tests/ "$@"
