#!/bin/bash
set -eu
test "$#" -eq 7
root="$1"
source_dir="$2"
commit="$3"
index="$4"
uuid="$5"
arm="$6"
seed="$7"
case "$arm" in FULL_TARGET|NEW_TRAJECTORY_LOSS_OFF) ;; *) exit 2 ;; esac
case "$seed" in 0|1|2) ;; *) exit 2 ;; esac
admission_started=$(date +%s)
deadline=$(( admission_started + 54420 ))
test "$(cat "$root/source_commit.txt")" = "$commit"
test -f "$root/prepare/RESULT.json"
test ! -e "$root/prepare/FAILED.json"
run="$root/seed_$seed/$arm"
test ! -e "$run"
export PYTHONPATH="$source_dir" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
cd "$source_dir"
python3 - "$root/prepare/RESULT.json" <<'PY'
import sys, time
from gpu import astra_goal_scale_train as driver
result = driver.source.read(sys.argv[1])
assert isinstance(driver.PROTOCOL_PATH, str) and isinstance(driver.PROTOCOL_SHA, str), 'scale_fit_protocol_not_bound'
assert result['schema'] == driver.SCHEMA and result['phase'] == 'prepare' and result['status'] == 'PREPARED_NO_MODEL'
assert result['row_count'] == 1758 and result['new_actual_train_targets'] == 1536 and result['probe_training_rows'] == 0
assert result['entry_sha256'] == driver.source.file_hash(driver.__file__) and result['protocol_sha256'] == driver.PROTOCOL_SHA
assert time.time() + 54420 < 1789980180 - 21600
PY
mkdir -p "$root/seed_$seed"
mkdir "$run"
launch="$run/launch"
mkdir "$launch"
python3 - "$root/prepare/RESULT.json" > "$launch/arguments.bin" <<'PY'
import json, sys
arguments = json.load(open(sys.argv[1]))['arguments']
for name in ('base_after', 'campaign', 'audit_root', 'repair_root', 'cycle_root', 'lesson_root',
             'transfer_root', 'bundle', 'bundle_sha', 'model_dir', 'shard_roots'):
    value = arguments[name]
    if value is not None:
        values = value if isinstance(value, list) else [value]
        for item in ['--' + name.replace('_', '-')] + values:
            assert isinstance(item, str) and '\0' not in item
            sys.stdout.buffer.write(item.encode() + b'\0')
PY
mapfile -d '' -t common < "$launch/arguments.bin"
clear=false
for attempt in 1 2 3 4 5 6; do
    if timeout 30 env CUDA_VISIBLE_DEVICES= python3 /tmp/astra_cue_sensitivity_20260914_attempt1/scanner.py "$index" "$uuid" < /tmp/astra_stage2a_reduced_20260914_attempt1/service_exceptions.json > "$launch/resource_${attempt}.json"; then
        clear=true
        break
    fi
    sleep 5
done
if test "$clear" != true || test "$(( $(date +%s) - admission_started ))" -gt 300; then
    date -u +%Y-%m-%dT%H:%M:%SZ > "$launch/GUARD_ABORT.txt"
    exit 1
fi
printf '%s\n' "$$" > "$launch/guardian_pid.txt"
printf '%s\n' "$commit" > "$launch/source_commit.txt"
printf '%s\n' "$deadline" > "$launch/deadline_epoch.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$launch/started_utc.txt"
export CUDA_VISIBLE_DEVICES="$uuid"
run_stage() {
    seconds="$1"
    shift
    remaining=$(( deadline - $(date +%s) - 60 ))
    test "$remaining" -gt 0
    if test "$seconds" -gt "$remaining"; then seconds="$remaining"; fi
    timeout --signal=INT --kill-after=60 "$seconds" /localhome/local-rohing/v2/venv/bin/python -B -m gpu.astra_goal_scale_train "${common[@]}" --gpu-uuid "$uuid" --arm "$arm" --seed "$seed" "$@"
}
run_stage 43200 --phase train --output "$run/train"
run_stage 10800 --phase after --training "$run/train" --output "$run/after"
date -u +%Y-%m-%dT%H:%M:%SZ > "$launch/completed_utc.txt"
