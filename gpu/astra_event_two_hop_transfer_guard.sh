#!/bin/bash
set -eu
test "$#" -eq 7
root="$1"
source_dir="$2"
commit="$3"
index="$4"
uuid="$5"
phase="$6"
arm="$7"
case "$phase:$arm" in
    collect:TRAINED) output="$root/collect"; launch="$root/launch_collect" ;;
    readout:TRAINED|readout:ORIGINAL) output="$root/$arm"; launch="$root/launch_$arm" ;;
    *) exit 2 ;;
esac
test -f "$root/prepare/RESULT.json"
test ! -e "$root/prepare/FAILED.json"
test ! -e "$output"
test "$(git -C "$source_dir" rev-parse HEAD)" = "$commit"
python3 -c 'import json,sys; assert json.load(open(sys.argv[1]))["status"] == "PREPARED_NO_MODEL"' "$root/prepare/RESULT.json"
extra=()
if test "$phase" = readout; then
    test ! -e "$root/collect/FAILED.json"
    python3 -c 'import json,sys; r=json.load(open(sys.argv[1])); assert r["status"] == "COMPLETE" and r["phase"] == "collect" and r["arm"] == "TRAINED" and r["model_calls"] == 8 and r["accepted_events"] == 4' "$root/collect/RESULT.json"
    extra=(--collection "$root/collect")
fi
mkdir "$launch"
clear=false
for attempt in 1 2 3 4 5 6; do
    if timeout 30 env CUDA_VISIBLE_DEVICES= python3 /tmp/astra_cue_sensitivity_20260914_attempt1/scanner.py "$index" "$uuid" < /tmp/astra_stage2a_reduced_20260914_attempt1/service_exceptions.json > "$launch/resource_${attempt}.json"; then
        clear=true
        break
    fi
    sleep 5
done
if test "$clear" != true; then
    date -u +%Y-%m-%dT%H:%M:%SZ > "$launch/GUARD_ABORT.txt"
    exit 1
fi
python3 -c 'import time; assert time.time()+1920 < 1789980180-21600'
printf '%s\n' "$$" > "$launch/guardian_pid.txt"
printf '%s\n' "$commit" > "$launch/source_commit.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$launch/started_utc.txt"
export PYTHONPATH="$source_dir" CUDA_VISIBLE_DEVICES="$uuid" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
timeout --signal=INT --kill-after=60 1860 /localhome/local-rohing/v2/venv/bin/python -B -m gpu.astra_event_two_hop_transfer \
    --base-after /tmp/astra_adult_cycle2_20260914_attempt1/CUE_REPLAY/corrective_sleep/CHILD_CORRECTIVE/after \
    --campaign /tmp/astra_reader_audit_lesson_20260914_attempt1 \
    --audit-root /tmp/astra_actual_reader_audit_20260914_attempt1 \
    --repair-root /tmp/astra_selected_reader_repair_20260914_attempt1 \
    --cycle-root /tmp/astra_fresh_reader_cycle_20260914_attempt2 \
    --lesson-root /tmp/astra_event_two_hop_lesson_20260914_attempt1 \
    --gpu-uuid "$uuid" --phase "$phase" --arm "$arm" "${extra[@]}" --output "$output"
date -u +%Y-%m-%dT%H:%M:%SZ > "$launch/completed_utc.txt"
