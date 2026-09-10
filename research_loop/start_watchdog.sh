#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORKFLOW="${1:-research_loop/workflows/dream_ladder_v5.json}"
cd "$ROOT"
mkdir -p .research_loop
nohup .venv/bin/python -m research_loop.watchdog "$WORKFLOW" \
    > .research_loop/watchdog.log 2>&1 </dev/null &
echo "$!"
