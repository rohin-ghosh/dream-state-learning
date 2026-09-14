#!/bin/bash
set -eu
sleep 3
root="$1"
source_dir="$2"
commit="$3"
index="$4"
uuid="$5"
stage="$6"
after=/tmp/astra_adult_cycle2_20260914_attempt1/CUE_REPLAY/corrective_sleep/CHILD_CORRECTIVE/after
case "$stage" in
    collect) duration=1920 ;;
    AUDIT_SFT|AUDIT_LOSS_OFF) duration=7440 ;;
    *) exit 2 ;;
esac
test -f "$root/prepare/RESULT.json"
test ! -e "$root/$stage"
mkdir "$root/launch_$stage"
clear=false
for attempt in 1 2 3 4 5 6; do
    if timeout 30 env CUDA_VISIBLE_DEVICES= python3 /tmp/astra_cue_sensitivity_20260914_attempt1/scanner.py "$index" "$uuid" < /tmp/astra_stage2a_reduced_20260914_attempt1/service_exceptions.json > "$root/launch_$stage/resource_${attempt}.json"; then
        clear=true
        break
    fi
    sleep 5
done
if test "$clear" != true; then
    date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch_$stage/GUARD_ABORT.txt"
    exit 1
fi
python3 -c 'import sys,time; assert time.time()+int(sys.argv[1]) < 1789980180-21600' "$duration"
printf '%s\n' "$$" > "$root/launch_$stage/guardian_pid.txt"
printf '%s\n' "$commit" > "$root/launch_$stage/source_commit.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch_$stage/started_utc.txt"
export PYTHONPATH="$source_dir" CUDA_VISIBLE_DEVICES="$uuid" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
python=/localhome/local-rohing/v2/venv/bin/python
common=(--after-source "$after" --gpu-uuid "$uuid")
if test "$stage" = collect; then
    timeout --signal=INT --kill-after=60 1860 "$python" -B -m gpu.astra_reader_audit_lesson "${common[@]}" --phase collect --output "$root/collect"
else
    test -f "$root/collect/RESULT.json"
    timeout --signal=INT --kill-after=60 5460 "$python" -B -m gpu.astra_reader_audit_lesson "${common[@]}" --phase train --arm "$stage" --lesson "$root/collect" --output "$root/$stage/train"
    timeout --signal=INT --kill-after=60 1860 "$python" -B -m gpu.astra_reader_audit_lesson "${common[@]}" --phase after --arm "$stage" --lesson "$root/collect" --training "$root/$stage/train" --output "$root/$stage/after"
fi
date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch_$stage/completed_utc.txt"
