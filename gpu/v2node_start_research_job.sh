#!/bin/bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
    echo "usage: $0 RUN_ID APPROVAL_SHA256" >&2
    exit 64
fi

RUN_ID="$1"
APPROVAL_SHA256="$2"
case "$RUN_ID" in
    *[!A-Za-z0-9._-]*|'') echo "invalid run id" >&2; exit 64 ;;
esac
case "$APPROVAL_SHA256" in
    *[!0-9a-f]*|'') echo "invalid approval sha256" >&2; exit 64 ;;
esac
if [ "${#APPROVAL_SHA256}" -ne 64 ]; then
    echo "invalid approval sha256 length" >&2
    exit 64
fi

PROJECT="$HOME/dream-state"
JOB_ROOT="/localhome/local-rohing/v2/jobs"
PYTHON="/localhome/local-rohing/v2/venv/bin/python"
VENV_BIN="/localhome/local-rohing/v2/venv/bin"
SPEC="research_loop/workflows/dream_ladder_v5.remote.json"
LOCK="research_loop/runtime/$RUN_ID.lock.json"
APPROVAL="research_loop/runtime/$RUN_ID.sol-review.json"

cd "$PROJECT"
mkdir -p "$JOB_ROOT"
nohup env PATH="$VENV_BIN:$PATH" PYTHONPATH=. \
    "$PYTHON" -m research_loop.remote_job run \
    --spec "$SPEC" --run-id "$RUN_ID" --job-root "$JOB_ROOT" \
    --lock "$LOCK" --approval "$APPROVAL" \
    --approval-sha256 "$APPROVAL_SHA256" \
    > "$JOB_ROOT/$RUN_ID.launcher.log" 2>&1 </dev/null &
sleep 5
exec env PYTHONPATH=. "$PYTHON" -m research_loop.remote_job status \
    --run-id "$RUN_ID" --job-root "$JOB_ROOT"
