#!/bin/bash
set -eu
sleep 3
campaign="$1"
source_dir="$2"
commit="$3"
index="$4"
uuid="$5"
arm="$6"
adapter="$7"
adapter_sha="$8"
root="$campaign/$arm"
mkdir "$root" "$root/launch_collect"
clear=false
for attempt in 1 2 3 4 5 6; do
    if timeout 30 env CUDA_VISIBLE_DEVICES= python3 /tmp/astra_cue_sensitivity_20260914_attempt1/scanner.py "$index" "$uuid" < /tmp/astra_stage2a_reduced_20260914_attempt1/service_exceptions.json > "$root/launch_collect/resource_${attempt}.json"; then
        clear=true
        break
    fi
    sleep 5
done
if test "$clear" != true; then
    date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch_collect/GUARD_ABORT.txt"
    exit 1
fi
python3 -c 'import time; assert time.time()+1920 < 1789980180-21600'
printf '%s\n' "$$" > "$root/launch_collect/guardian_pid.txt"
printf '%s\n' "$commit" > "$root/launch_collect/source_commit.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch_collect/started_utc.txt"
export PYTHONPATH="$source_dir" CUDA_VISIBLE_DEVICES="$uuid" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
timeout --signal=INT --kill-after=60 1860 /localhome/local-rohing/v2/venv/bin/python -B -m gpu.astra_experienced_event_adult_cycle \
    --phase collect --development-arm "$arm" --initial-adapter-dir "$adapter" \
    --expected-initial-adapter-sha256 "$adapter_sha" --gpu-uuid "$uuid" \
    --model-dir /localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28 \
    --expected-base-sha256 a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992 \
    --collection /tmp/astra_microloop_20260914_attempt2/collection \
    --cue-collection /tmp/astra_cue_lastturn_20260914_attempt1/run --output "$root/collect"
date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch_collect/completed_utc.txt"
