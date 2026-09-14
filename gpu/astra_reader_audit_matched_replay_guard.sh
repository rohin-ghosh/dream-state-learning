#!/bin/bash
set -eu
sleep 3
root="$1"
source_dir="$2"
commit="$3"
index="$4"
uuid="$5"
arm="$6"
case "$arm" in AUDIT_SFT|AUDIT_LOSS_OFF) ;; *) exit 2 ;; esac
test -f "$root/prepare_$arm/RESULT.json"
test ! -e "$root/$arm"
mkdir "$root/launch_$arm"
clear=false
for attempt in 1 2 3 4 5 6; do
    if timeout 30 env CUDA_VISIBLE_DEVICES= python3 /tmp/astra_cue_sensitivity_20260914_attempt1/scanner.py "$index" "$uuid" < /tmp/astra_stage2a_reduced_20260914_attempt1/service_exceptions.json > "$root/launch_$arm/resource_${attempt}.json"; then
        clear=true
        break
    fi
    sleep 5
done
if test "$clear" != true; then
    date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch_$arm/GUARD_ABORT.txt"
    exit 1
fi
python3 -c 'import time; assert time.time()+1920 < 1789980180-21600'
printf '%s\n' "$$" > "$root/launch_$arm/guardian_pid.txt"
printf '%s\n' "$commit" > "$root/launch_$arm/source_commit.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch_$arm/started_utc.txt"
export PYTHONPATH="$source_dir" CUDA_VISIBLE_DEVICES="$uuid" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
timeout --signal=INT --kill-after=60 1860 /localhome/local-rohing/v2/venv/bin/python -B -m gpu.astra_reader_audit_matched_replay \
    --after-source /tmp/astra_adult_cycle2_20260914_attempt1/CUE_REPLAY/corrective_sleep/CHILD_CORRECTIVE/after \
    --campaign /tmp/astra_reader_audit_lesson_20260914_attempt1 \
    --stimulus-root /tmp/astra_fresh_reader_cycle_20260914_attempt2 \
    --arm "$arm" --gpu-uuid "$uuid" --output "$root/$arm"
date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch_$arm/completed_utc.txt"
