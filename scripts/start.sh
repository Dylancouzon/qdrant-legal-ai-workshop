#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
runner=(uv run --frozen)
if [[ -f .env ]]; then runner+=(--env-file .env); fi
"${runner[@]}" python -m workshop.cli ready
exec "${runner[@]}" python -m workshop.serve
