#!/bin/bash
set -eu
test "$#" -eq 6
root="$1"
source_dir="$2"
commit="$3"
index="$4"
uuid="$5"
arm="$6"
case "$arm:$index" in BASELINE:0|FULL_TARGET:0|NEW_TRAJECTORY_LOSS_OFF:1) ;; *) exit 2 ;; esac
admission_started=$(date +%s)
budget=14760
if test "$arm" = BASELINE; then budget=3960; fi
deadline=$(( admission_started + budget ))
test "$(cat "$root/source_commit.txt")" = "$commit"
test -f "$root/prepare/RESULT.json"
test ! -e "$root/prepare/FAILED.json"
run="$root/$arm"
if test "$arm" = BASELINE; then
    test ! -e "$root/baseline"
    test ! -L "$root/baseline"
else
    test -f "$root/baseline/RESULT.json"
    test ! -e "$root/baseline/FAILED.json"
fi
test ! -e "$run"
test ! -L "$run"
export PYTHONPATH="$source_dir" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
python3 - "$root/prepare/RESULT.json" "$budget" <<'PY'
import datetime
import sys
import time
from gpu import astra_goal_quality_train as driver
result = driver.source.read(sys.argv[1])
assert result['schema'] == driver.SCHEMA and result['phase'] == 'prepare' and result['status'] == 'PREPARED_NO_MODEL'
assert result['row_count'] == 1674 and result['new_actual_train_targets'] == 1452 and result['probe_training_rows'] == 0
assert result['seed'] == 0 and result['model_calls'] == result['fits'] == result['updates'] == 0
assert result['entry_sha256'] == driver.source.file_hash(driver.__file__) and result['protocol_sha256'] == driver.PROTOCOL_SHA
driver.same(result['binding']['helper_hashes'], driver.helpers(), 'published_quality_source_drift')
lease = datetime.datetime(2026, 9, 26, 3, 3, tzinfo=datetime.timezone.utc).timestamp()
assert time.time() + int(sys.argv[2]) < lease - 21600
PY
mkdir "$run"
launch="$run/launch"
mkdir "$launch"
python3 - "$root/prepare/RESULT.json" > "$launch/arguments.bin" <<'PY'
import json
import sys
arguments = json.load(open(sys.argv[1]))['arguments']
for name in ('base_after', 'campaign', 'audit_root', 'repair_root', 'cycle_root', 'lesson_root',
             'transfer_root', 'bundle', 'bundle_sha', 'model_dir', 'shard_roots', 'quality_root', 'unit_roots'):
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
    if timeout 30 env CUDA_VISIBLE_DEVICES= python3 /tmp/astra_goal_scale_20260914_attempt1/scanner.py "$index" "$uuid" < /tmp/astra_goal_scale_20260914_attempt1/service_exceptions.json > "$launch/resource_${attempt}.json"; then
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
child=
stop_child() {
    if test -n "$child"; then kill -INT "$child" 2>/dev/null || true; wait "$child" 2>/dev/null || true; fi
    date -u +%Y-%m-%dT%H:%M:%SZ > "$launch/GUARD_ABORT.txt"
    exit 1
}
trap stop_child INT TERM
run_stage() {
    seconds="$1"
    shift
    remaining=$(( deadline - $(date +%s) - 60 ))
    test "$remaining" -gt 0
    if test "$seconds" -gt "$remaining"; then seconds="$remaining"; fi
    command=(timeout --signal=INT --kill-after=60 "$seconds" /localhome/local-rohing/v2/venv/bin/python -B -m gpu.astra_goal_quality_train "${common[@]}" --gpu-uuid "$uuid" --seed 0 "$@")
    printf '%q ' "${command[@]}" >> "$launch/commands.txt"
    printf '\n' >> "$launch/commands.txt"
    "${command[@]}" &
    child=$!
    printf '%s\n' "$child" >> "$launch/stage_pids.txt"
    if ! wait "$child"; then
        date -u +%Y-%m-%dT%H:%M:%SZ > "$launch/GUARD_ABORT.txt"
        exit 1
    fi
    child=
}
if test "$arm" = BASELINE; then
    run_stage 3600 --phase baseline --output "$root/baseline"
else
    run_stage 10800 --phase train --arm "$arm" --baseline "$root/baseline" --output "$run/train"
    run_stage 3600 --phase after --arm "$arm" --baseline "$root/baseline" --training "$run/train" --output "$run/after"
fi
date -u +%Y-%m-%dT%H:%M:%SZ > "$launch/completed_utc.txt"
