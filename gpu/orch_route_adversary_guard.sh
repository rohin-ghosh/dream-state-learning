#!/bin/bash
set -eu
test "$#" -eq 7
root="$1"
commit="$2"
archive="$3"
prepare_sha="$4"
arm="$5"
index="$6"
uuid="$7"
case "$arm:$index" in FULL_TARGET:2|NEW_TRAJECTORY_LOSS_OFF:3|ORIGINAL37EC:4) ;; *) exit 2 ;; esac
export PYTHONPATH="$root/source" PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
unset CUDA_VISIBLE_DEVICES
python3 -B -m gpu.orch_route_adversary --phase scan --root "$root" --gpu-index "$index" --gpu-uuid "$uuid" > "$root/${arm}_physical_scan.json"
test ! -e "$root/$arm"
printf '%s\n' "$$" > "$root/${arm}_guardian_pid.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$root/${arm}_started_utc.txt"
export CUDA_VISIBLE_DEVICES="$uuid"
if timeout --signal=INT --kill-after=30 2400 /localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_route_adversary \
    --phase run --root "$root" --commit "$commit" --archive "$archive" --prepare-sha "$prepare_sha" \
    --arm "$arm" --gpu-index "$index" --gpu-uuid "$uuid"; then
    date -u +%Y-%m-%dT%H:%M:%SZ > "$root/${arm}_completed_utc.txt"
else
    date -u +%Y-%m-%dT%H:%M:%SZ > "$root/${arm}_GUARD_ABORT.txt"
    exit 1
fi
