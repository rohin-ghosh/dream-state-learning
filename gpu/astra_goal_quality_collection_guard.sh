#!/bin/bash
set -eu
test "$#" -eq 6
root="$1"
source_dir="$2"
commit="$3"
index="$4"
uuid="$5"
unit="$6"
case "$unit" in 0|1|4|6) ;; *) exit 2 ;; esac
started=$(date +%s)
deadline=$(( started + 3960 ))
test "$(cat "$root/source_commit.txt")" = "$commit"
test -f "$root/prepare/RESULT.json"
test ! -e "$root/prepare/FAILED.json"
run="$root/unit$unit"
test ! -e "$run"
export PYTHONPATH="$source_dir" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
python3 - "$root/prepare/RESULT.json" <<'PY'
import datetime
import json
import sys
import time
from gpu import astra_goal_quality_collection as driver
result = json.load(open(sys.argv[1]))
assert result['schema'] == driver.SCHEMA and result['status'] == 'PREPARED_NO_MODEL'
assert result['phase'] == 'prepare' and result['model_calls'] == result['fits'] == result['updates'] == 0
assert result['entry_sha256'] == driver.source.file_hash(driver.__file__)
assert result['protocol_sha256'] == driver.PROTOCOL_SHA
assert result['reused_candidate_rows'] == 756 and result['new_worlds'] == 29
assert result['eligible_train_worlds'] == 61 and result['max_new_calls'] == 696
lease = datetime.datetime(2026, 9, 26, 3, 3, tzinfo=datetime.timezone.utc).timestamp()
assert time.time() + 3960 < lease - 21600
PY
mkdir "$run"
mkdir "$run/launch"
clear=false
for attempt in 1 2 3 4 5 6; do
    if timeout 30 env CUDA_VISIBLE_DEVICES= python3 /tmp/astra_goal_scale_20260914_attempt1/scanner.py "$index" "$uuid" < /tmp/astra_goal_scale_20260914_attempt1/service_exceptions.json > "$run/launch/resource_${attempt}.json"; then
        clear=true
        break
    fi
    sleep 5
done
if test "$clear" != true || test "$(( $(date +%s) - started ))" -gt 300; then
    date -u +%Y-%m-%dT%H:%M:%SZ > "$run/launch/GUARD_ABORT.txt"
    exit 1
fi
python3 - "$root/prepare/RESULT.json" > "$run/launch/arguments.bin" <<'PY'
import json
import sys
arguments = json.load(open(sys.argv[1]))['arguments']
for name in ('bundle', 'bundle_sha', 'model_dir', 'shard_roots'):
    value = arguments[name]
    values = value if isinstance(value, list) else [value]
    for item in ['--' + name.replace('_', '-')] + values:
        assert isinstance(item, str) and '\0' not in item
        sys.stdout.buffer.write(item.encode() + b'\0')
PY
mapfile -d '' -t common < "$run/launch/arguments.bin"
printf '%s\n' "$$" > "$run/launch/guardian_pid.txt"
printf '%s\n' "$commit" > "$run/launch/source_commit.txt"
printf '%s\n' "$deadline" > "$run/launch/deadline_epoch.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$run/launch/started_utc.txt"
export CUDA_VISIBLE_DEVICES="$uuid"
remaining=$(( deadline - $(date +%s) - 60 ))
test "$remaining" -gt 0
seconds=3600
if test "$seconds" -gt "$remaining"; then seconds="$remaining"; fi
timeout --signal=INT --kill-after=60 "$seconds" /localhome/local-rohing/v2/venv/bin/python -B -m gpu.astra_goal_quality_collection "${common[@]}" --gpu-uuid "$uuid" --phase collect --unit "$unit" --output "$run/collect"
date -u +%Y-%m-%dT%H:%M:%SZ > "$run/launch/completed_utc.txt"
