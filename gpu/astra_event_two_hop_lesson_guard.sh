#!/bin/bash
set -eu
sleep 3
root="$1"
source_dir="$2"
commit="$3"
index="$4"
uuid="$5"
test -f "$root/prepare/RESULT.json"
test ! -e "$root/collect"
test ! -e "$root/train"
test ! -e "$root/after"
mkdir "$root/launch"
clear=false
for attempt in 1 2 3 4 5 6; do
    if timeout 30 env CUDA_VISIBLE_DEVICES= python3 /tmp/astra_cue_sensitivity_20260914_attempt1/scanner.py "$index" "$uuid" < /tmp/astra_stage2a_reduced_20260914_attempt1/service_exceptions.json > "$root/launch/resource_${attempt}.json"; then
        clear=true
        break
    fi
    sleep 5
done
if test "$clear" != true; then
    date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch/GUARD_ABORT.txt"
    exit 1
fi
python3 -c 'import time; assert time.time()+9300 < 1789980180-21600'
printf '%s\n' "$$" > "$root/launch/guardian_pid.txt"
printf '%s\n' "$commit" > "$root/launch/source_commit.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch/started_utc.txt"
export PYTHONPATH="$source_dir" CUDA_VISIBLE_DEVICES="$uuid" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
common=(--base-after /tmp/astra_adult_cycle2_20260914_attempt1/CUE_REPLAY/corrective_sleep/CHILD_CORRECTIVE/after
    --campaign /tmp/astra_reader_audit_lesson_20260914_attempt1
    --audit-root /tmp/astra_actual_reader_audit_20260914_attempt1
    --repair-root /tmp/astra_selected_reader_repair_20260914_attempt1
    --cycle-root /tmp/astra_fresh_reader_cycle_20260914_attempt2 --gpu-uuid "$uuid"
    --event-collection /tmp/astra_event_two_hop_20260914_attempt1/collect
    --baseline /tmp/astra_event_two_hop_turnbound_20260914_attempt1/readout)
python=/localhome/local-rohing/v2/venv/bin/python
timeout --signal=INT --kill-after=60 1860 "$python" -B -m gpu.astra_event_two_hop_lesson "${common[@]}" --phase collect --output "$root/collect"
timeout --signal=INT --kill-after=60 3600 "$python" -B -m gpu.astra_event_two_hop_lesson "${common[@]}" --phase train --lessons "$root/collect" --output "$root/train"
timeout --signal=INT --kill-after=60 3600 "$python" -B -m gpu.astra_event_two_hop_lesson "${common[@]}" --phase after --lessons "$root/collect" --training "$root/train" --output "$root/after"
date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch/completed_utc.txt"
