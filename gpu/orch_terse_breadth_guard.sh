#!/bin/bash
set -euo pipefail
test "$#" -eq 7
root="$1"
lane="$2"
phase="$3"
source_sha="$4"
publication="$5"
manifest_sha="$6"
model="$7"
case "$root" in /tmp/orch_terse_breadth_20260914_attempt[0-9]*) ;; *) exit 2 ;; esac
case "$lane" in 0|1|2|3|4|5) ;; *) exit 2 ;; esac
case "$phase" in collect|baseline|train|after) ;; *) exit 2 ;; esac
test "$(cat "$root/PUBLISHED_PRELAUNCH_COMMIT.txt")" = "$publication"
test "$(sha256sum "$root/source.tar.gz" | cut -d' ' -f1)" = "$source_sha"
test "$(sha256sum "$root/prepare/MANIFEST.json" | cut -d' ' -f1)" = "$manifest_sha"
test "$(sha256sum "$root/scanner.py" | cut -d' ' -f1)" = 6ed5c48c144dcf26dcb856798ab31d69e39bc66b6780211f2b10553972f8519b
test "$(sha256sum "$root/service_exceptions.json" | cut -d' ' -f1)" = "$(cat "$root/SERVICE_EXCEPTIONS_SHA.txt")"
export PYTHONPATH="$root/source" PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
read -r host index uuid < <(python3 - "$lane" <<'PY'
import sys
from gpu.orch_terse_breadth_run import ALLOCATION
print(*ALLOCATION[int(sys.argv[1])][:3])
PY
)
if test "$host" = a100; then
    test "$(hostname)" = a4u8g-0147
    lease=$(date -u -d '2026-09-26 23:05:00 UTC' +%s)
else
    test "$(hostname)" = ipp2-ovx-p6-09
    lease=$(date -u -d '2026-09-19 21:03:00 UTC' +%s)
fi
started=$(date +%s)
budget=7200
if test "$phase" = train; then budget=86400; fi
deadline=$(( started + budget ))
lifetime=$(cat "$root/ALLOCATION_DEADLINE_EPOCH.txt")
test "$deadline" -lt "$lease"
test "$deadline" -lt "$lifetime"
stage="$phase$lane"
if test "$phase" = collect; then stage="collection$lane"; fi
launch="$root/launch_$stage"
mkdir "$launch"
test ! -e "$root/$stage"
printf '%s\n' "$$" > "$launch/guardian_pid.txt"
printf '%s\n' "$deadline" > "$launch/deadline_epoch.txt"
date -u +%FT%TZ > "$launch/started_utc.txt"
python3 - "$index" "$uuid" > "$launch/GPU_UUID_CHECK.json" <<'PY'
import json
import subprocess
import sys
rows = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid', '--format=csv,noheader'], text=True)
assert [sys.argv[1], sys.argv[2]] in [list(map(str.strip, row.split(','))) for row in rows.splitlines()]
print(json.dumps({'index': int(sys.argv[1]), 'uuid': sys.argv[2], 'all_gpus': rows}))
PY
timeout 30 python3 "$root/scanner.py" "$index" "$uuid" < "$root/service_exceptions.json" > "$launch/RESOURCE.json"
if test "$phase" != collect; then
    test -f "$root/assembly/BATCH.json"
    test "$(sha256sum "$root/assembly/BATCH.json" | cut -d' ' -f1)" = "$(cat "$root/BATCH_ADMITTED_SHA.txt")"
fi
remaining=$(( deadline - $(date +%s) - 60 ))
test "$remaining" -gt 0
set +e
timeout --signal=INT --kill-after=30 "$remaining" env CUDA_VISIBLE_DEVICES="$uuid" \
    /localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_terse_breadth_run \
    --root "$root" --phase "$phase" --lane "$lane" --model-dir "$model" \
    --output "$root/$stage" --deadline "$(( deadline - 60 ))" > "$launch/native.log" 2>&1
exit_code=$?
printf '%s\n' "$exit_code" > "$launch/exit_code.txt"
date -u +%FT%TZ > "$launch/completed_utc.txt"
exit "$exit_code"
