#!/bin/bash
set -eu
test "$#" -eq 6
root="$1"
source_dir="$2"
commit="$3"
index="$4"
uuid="$5"
shard="$6"
started=$(date +%s)
deadline=$(( started + 3960 ))
test "$(cat "$root/source_commit.txt")" = "$commit"
test ! -e "$root/teach"
export PYTHONPATH="$source_dir" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1
python3 - "$root/prepare/RESULT.json" "$shard" <<'PY'
import json
import sys
import time
from gpu import astra_rich_action_first_v3_collection as driver
result = json.load(open(sys.argv[1]))
assert result['schema'] == driver.SCHEMA and result['status'] == 'PREPARED_NO_MODEL'
assert result['phase'] == 'prepare' and result['shard'] == int(sys.argv[2])
assert result['model_calls'] == result['fits'] == result['updates'] == 0
assert result['entry_sha256'] == driver.source.file_hash(driver.__file__)
assert result['protocol_sha256'] == driver.PROTOCOL_SHA
assert time.time() + 3960 < 1790380800 - 21600
PY
mkdir "$root/launch"
clear=false
for attempt in 1 2 3 4 5 6; do
    if timeout 30 env CUDA_VISIBLE_DEVICES= python3 /tmp/astra_rich_collection_20260914_attempt1/scanner.py "$index" "$uuid" < /tmp/astra_rich_collection_20260914_attempt1/service_exceptions.json > "$root/launch/resource_${attempt}.json"; then
        clear=true
        break
    fi
    sleep 5
done
if test "$clear" != true || test "$(( $(date +%s) - started ))" -gt 300; then
    date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch/GUARD_ABORT.txt"
    exit 1
fi
python3 - "$root/prepare/RESULT.json" > "$root/launch/arguments.bin" <<'PY'
import json
import sys
arguments = json.load(open(sys.argv[1]))['arguments']
for name in ('bundle','bundle_sha','model_dir','exposure','shard'):
    for item in ['--'+name.replace('_','-'),str(arguments[name])]:
        assert '\0' not in item
        sys.stdout.buffer.write(item.encode()+b'\0')
PY
mapfile -d '' -t common < "$root/launch/arguments.bin"
printf '%s\n' "$$" > "$root/launch/guardian_pid.txt"
printf '%s\n' "$commit" > "$root/launch/source_commit.txt"
printf '%s\n' "$deadline" > "$root/launch/deadline_epoch.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch/started_utc.txt"
export CUDA_VISIBLE_DEVICES="$uuid"
remaining=$(( deadline - $(date +%s) - 60 ))
test "$remaining" -gt 0
seconds=3600
if test "$seconds" -gt "$remaining"; then seconds="$remaining"; fi
timeout --signal=INT --kill-after=60 "$seconds" /localhome/local-rohing/v2/venv/bin/python -B -m gpu.astra_rich_action_first_v3_collection "${common[@]}" --gpu-uuid "$uuid" --phase teach --output "$root/teach"
date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch/completed_utc.txt"
