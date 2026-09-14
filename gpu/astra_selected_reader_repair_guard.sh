#!/bin/bash
set -eu
sleep 3
root="$1"
source_dir="$2"
commit="$3"
index="$4"
uuid="$5"
parent_arm="$6"
material_arm="$7"
case "$parent_arm" in AUDIT_SFT|AUDIT_LOSS_OFF) ;; *) exit 2 ;; esac
case "$material_arm" in SELECTED|UNIFORM) ;; *) exit 2 ;; esac
cell="${parent_arm}_${material_arm}"
test -f "$root/prepare_$cell/RESULT.json"
test ! -e "$root/$cell"
mkdir "$root/launch_$cell"
clear=false
for attempt in 1 2 3 4 5 6; do
    if timeout 30 env CUDA_VISIBLE_DEVICES= python3 /tmp/astra_cue_sensitivity_20260914_attempt1/scanner.py "$index" "$uuid" < /tmp/astra_stage2a_reduced_20260914_attempt1/service_exceptions.json > "$root/launch_$cell/resource_${attempt}.json"; then
        clear=true
        break
    fi
    sleep 5
done
if test "$clear" != true; then
    date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch_$cell/GUARD_ABORT.txt"
    exit 1
fi
python3 -c 'import time; assert time.time()+7440 < 1789980180-21600'
printf '%s\n' "$$" > "$root/launch_$cell/guardian_pid.txt"
printf '%s\n' "$commit" > "$root/launch_$cell/source_commit.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch_$cell/started_utc.txt"
export PYTHONPATH="$source_dir" CUDA_VISIBLE_DEVICES="$uuid" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
python=/localhome/local-rohing/v2/venv/bin/python
common=(--base-after /tmp/astra_adult_cycle2_20260914_attempt1/CUE_REPLAY/corrective_sleep/CHILD_CORRECTIVE/after
    --campaign /tmp/astra_reader_audit_lesson_20260914_attempt1
    --audit-root /tmp/astra_actual_reader_audit_20260914_attempt1
    --parent-arm "$parent_arm" --material-arm "$material_arm" --gpu-uuid "$uuid")
timeout --signal=INT --kill-after=60 5460 "$python" -B -m gpu.astra_selected_reader_repair "${common[@]}" --phase train --output "$root/$cell/train"
timeout --signal=INT --kill-after=60 1860 "$python" -B -m gpu.astra_selected_reader_repair "${common[@]}" --phase after --training "$root/$cell/train" --output "$root/$cell/after"
date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch_$cell/completed_utc.txt"
