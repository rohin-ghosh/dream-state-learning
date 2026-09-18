#!/bin/bash
set -eu
REPOSITORY=/data/home/rohing/dream-state-orch
OUTPUT="$REPOSITORY/research_loop/workers/r158_kernel_execution_20260917"
REMOTE=/localhome/local-rohing/orch_r158_kernel_execution_20260917t0402z
mkdir "$OUTPUT/observer_v2_collection"
for attempt in $(seq 1 32); do
    stamp=$(date -u +%Y%m%dT%H%M%SZ)
    receipt="$OUTPUT/observer_v2_collection/$stamp.json"
    if ! bash "$REPOSITORY/gpu/a40r_ssh.sh" "cat $REMOTE/astra_nudge_observation_v2/STATUS.json" > "$receipt.partial"; then
        printf '%s remote fetch failed; no action or retry\n' "$stamp" > "$OUTPUT/observer_v2_collection/FAILED.txt"
        exit 1
    fi
    jq -e '.observer_only_no_publication_or_dispatch == true and (.observed_unix | type == "number")' "$receipt.partial" >/dev/null
    mv "$receipt.partial" "$receipt"
    cp "$receipt" "$OUTPUT/NUDGE_OBSERVATION_LATEST.json.next"
    mv "$OUTPUT/NUDGE_OBSERVATION_LATEST.json.next" "$OUTPUT/NUDGE_OBSERVATION_LATEST.json"
    if ! jq -e --argjson now "$(date +%s)" '$now - .observed_unix < 90' "$receipt" >/dev/null; then
        printf '%s remote observation stale; no liveness claim\n' "$stamp" > "$OUTPUT/observer_v2_collection/FAILED.txt"
        exit 1
    fi
    if jq -e '.campaign_closure != null and .campaign_closure.status != "TERMINAL_PRESENT_PROCESS_EXIT_PENDING"' "$receipt" >/dev/null; then
        bash "$REPOSITORY/gpu/a40r_ssh.sh" "tar -C $REMOTE -czf - FINISHED.json lane0/FINISHED.json lane4/FINISHED.json lane0/phase_02/TERMINAL.json lane4/phase_02/TERMINAL.json lane0/phase_02/service/STATE.json lane4/phase_02/service/STATE.json astra_nudge_observation_v2/STATUS.json" > "$OUTPUT/FINAL_CLOSURE_RECEIPTS.tar.gz"
        mkdir "$OUTPUT/final_closure_receipts"
        tar -xzf "$OUTPUT/FINAL_CLOSURE_RECEIPTS.tar.gz" -C "$OUTPUT/final_closure_receipts"
        jq -r '.campaign_closure.status' "$receipt" > "$OUTPUT/observer_v2_collection/FINISHED.txt"
        exit 0
    fi
    sleep 30
done
date -u '+%Y-%m-%dT%H:%M:%SZ bounded local observation ended; no forced closure' > "$OUTPUT/observer_v2_collection/BOUND_ENDED.txt"
