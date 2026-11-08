#!/usr/bin/env bash
set -euo pipefail
DEMO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$DEMO_DIR"
if [[ -n "${DEMO_PYTHON:-}" ]]; then
  exec "$DEMO_PYTHON" launch.py "$@"
elif [[ -x "$DEMO_DIR/.venv/bin/python" ]]; then
  exec "$DEMO_DIR/.venv/bin/python" launch.py "$@"
else
  exec python3 launch.py "$@"
fi
