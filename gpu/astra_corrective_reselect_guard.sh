#!/bin/bash
set -eu
sleep 3
root="$1"
source_dir="$2"
commit="$3"
index="$4"
uuid="$5"
recipe="${6:-original}"
test -f "$root/prepare/RESULT.json"
test ! -e "$root/run"
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
python3 -c 'import time; assert time.time()+1920 < 1789980180-21600'
printf '%s\n' "$$" > "$root/launch/guardian_pid.txt"
printf '%s\n' "$commit" > "$root/launch/source_commit.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch/started_utc.txt"
export PYTHONPATH="$source_dir" CUDA_VISIBLE_DEVICES="$uuid" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
timeout --signal=INT --kill-after=60 1860 /localhome/local-rohing/v2/venv/bin/python -B "$root/source/astra_corrective_reselect.py" \
    --after /tmp/astra_adult_cycle2_20260914_attempt1/CUE_REPLAY/corrective_sleep/CHILD_CORRECTIVE/after \
    --output "$root/run" --gpu-uuid "$uuid" --recipe "$recipe"
date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch/completed_utc.txt"
