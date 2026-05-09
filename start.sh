#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ -f "${HOME}/AI/brain/venv/bin/activate" ]]; then
  # shellcheck source=/dev/null
  source "${HOME}/AI/brain/venv/bin/activate"
elif [[ -d ".venv" ]]; then
  # shellcheck source=/dev/null
  source ".venv/bin/activate"
fi
exec python3 main.py "$@"
