#!/usr/bin/env bash
set -euo pipefail
test "$#" -eq 4
PLAN="$1"
PLAN_HASH="$2"
SIDE="$3"
GPU_UUID="$4"
case "$SIDE" in OLD|NEW) ;; *) exit 2 ;; esac
test "${CUDA_VISIBLE_DEVICES-}" = "$GPU_UUID"
ROOT="$(dirname "$PLAN")"
COMMAND_ROOT="$ROOT/$SIDE.command"
mkdir "$COMMAND_ROOT"
STARTED="$(date +%s)"
printf '{"shell_pid":%s,"started_unix":%s,"side":"%s","timeout_seconds":330,"kill_after_seconds":10}\n' "$$" "$STARTED" "$SIDE" > "$COMMAND_ROOT/started.json"
if timeout --signal=TERM --kill-after=10s 330s \
    /localhome/local-rohing/v2/venv/bin/python -B \
    /tmp/astra_native_parity_source_20260913_attempt1/astra_additive_native_parity_probe.py \
    worker --plan-path "$PLAN" --plan-sha256 "$PLAN_HASH" --path "$SIDE" --allow-native \
    > "$COMMAND_ROOT/stdout.log" 2> "$COMMAND_ROOT/stderr.log"; then
    RETURN_CODE=0
else
    RETURN_CODE=$?
fi
FINISHED="$(date +%s)"
printf '{"returncode":%s,"finished_unix":%s,"elapsed_seconds":%s}\n' "$RETURN_CODE" "$FINISHED" "$((FINISHED-STARTED))" > "$COMMAND_ROOT/exit.json"
cat "$COMMAND_ROOT/started.json" "$COMMAND_ROOT/exit.json"
exit "$RETURN_CODE"
