#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v uv >/dev/null || { echo "Install uv: https://docs.astral.sh/uv/getting-started/installation/"; exit 1; }
uv sync --frozen
runner=(uv run --frozen)
if [[ -f .env ]]; then runner+=(--env-file .env); fi
local_qdrant=$("${runner[@]}" python -c 'import os,urllib.parse; print(urllib.parse.urlparse(os.getenv("QDRANT_URL", "http://127.0.0.1:6333")).hostname in ("localhost", "127.0.0.1", "::1"))')
if [[ "$local_qdrant" == "True" ]]; then
  docker compose up -d
  for attempt in $(seq 1 30); do
    if curl --fail --silent http://127.0.0.1:6333/readyz >/dev/null; then break; fi
    sleep 1
  done
fi
"${runner[@]}" python -m workshop.cli prepare
"${runner[@]}" python -m workshop.cli ready
./scripts/prepare-model.sh
