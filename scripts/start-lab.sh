#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v uv >/dev/null || { echo "Install uv first: https://docs.astral.sh/uv/getting-started/installation/"; exit 1; }
lab_env_file="${1:-.env}"
if [[ ! -f "$lab_env_file" ]]; then
  echo "Copy .env.cloud.example to .env and enter the organizer's collection endpoint and read-only key. For local Docker, use .env.example instead."
  exit 1
fi
uv run --frozen --env-file "$lab_env_file" python -m workshop.cli connect
export APP_HOST=127.0.0.1
exec uv run --frozen --env-file "$lab_env_file" python -m workshop.serve
