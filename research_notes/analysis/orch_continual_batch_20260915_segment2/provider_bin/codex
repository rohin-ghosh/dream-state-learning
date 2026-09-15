#!/bin/bash
set -euo pipefail
[[ "${1:-}" == exec ]]
exec "${ORCH_CONTINUAL_BATCH_CODEX_REAL:?}" exec --json "${@:2}"
