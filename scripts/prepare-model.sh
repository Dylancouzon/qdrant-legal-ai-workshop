#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
runner=(uv run --frozen)
if [[ -f .env ]]; then runner+=(--env-file .env); fi
"${runner[@]}" python - <<'PY'
import os
import shutil
import subprocess
from workshop.provider import settings, status
provider, model = settings()
if provider == 'ollama' and not status()['available']:
    if not shutil.which('ollama'):
        raise SystemExit('Install and start Ollama on the facilitator machine, then rerun model preparation.')
    child_env = dict(os.environ, OLLAMA_HOST=os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434'))
    subprocess.run(['ollama', 'pull', model], check=True, env=child_env)
info = status()
if not info['available']:
    raise SystemExit('The configured model is unavailable. Check facilitator model settings; no successful readiness was recorded.')
print(f"Model ready: {info['mode']} / {info['model'] or 'explicit evidence-only mode'}")
PY
