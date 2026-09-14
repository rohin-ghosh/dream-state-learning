#!/bin/bash
set -euo pipefail
test "$#" -eq 5
root="$1"
index="$2"
uuid="$3"
source_sha="$4"
publication="$5"
test "$root" = /tmp/orch_text_prerequisite_20260914_attempt1
case "$index" in 0|1|2|3) ;; *) exit 2 ;; esac
shard="$root/shard$index"
mkdir "$shard"
started=$(date +%s)
deadline=$(( started + 1800 ))
lease_end=$(date -u -d '2026-09-27 05:05:00 UTC' +%s)
test "$deadline" -lt "$(( lease_end - 21600 ))"
test "$(cat "$root/PUBLISHED_PRELAUNCH_COMMIT.txt")" = "$publication"
test "$(sha256sum "$root/source.tar.gz" | cut -d' ' -f1)" = "$source_sha"
export PYTHONPATH="$root/source" PYTHONDONTWRITEBYTECODE=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python3 - "$root/prepare/RESULT.json" "$index" "$uuid" <<'PY'
import json
import subprocess
import sys
result = json.load(open(sys.argv[1]))
assert result['status'] == 'PREPARED_NO_GPU' and result['model_calls'] == 0
physical = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid', '--format=csv,noheader'], text=True)
assert [sys.argv[2], sys.argv[3]] in [line.replace(' ', '').split(',') for line in physical.splitlines()]
PY
test "$(sha256sum "$root/scanner.py" | cut -d' ' -f1)" = 6ed5c48c144dcf26dcb856798ab31d69e39bc66b6780211f2b10553972f8519b
test "$(sha256sum "$root/service_exceptions.json" | cut -d' ' -f1)" = 4a96b33797ab47ed7a1685de0ffe6c7ec4d210c143b720b85519b0ca05265391
timeout 30 env CUDA_VISIBLE_DEVICES= python3 "$root/scanner.py" "$index" "$uuid" < "$root/service_exceptions.json" > "$shard/RESOURCE.json"
printf '%s\n' "$$" > "$shard/guardian_pid.txt"
printf '%s\n' "$deadline" > "$shard/deadline_epoch.txt"
date -u +%FT%TZ > "$shard/started_utc.txt"
export CUDA_VISIBLE_DEVICES="$uuid"
remaining=$(( deadline - $(date +%s) - 60 ))
test "$remaining" -gt 0
set +e
timeout --signal=INT --kill-after=30 "$remaining" /localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_text_prerequisite_run \
    --phase screen --games "$root/games_v2" --env-python "$root/env/bin/python" \
    --bundle /tmp/astra_portable_37ec_20260914_attempt1 \
    --model-dir /localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28 \
    --source-archive "$root/source.tar.gz" --source-sha "$source_sha" \
    --output "$shard/screen" --shard "$index" --gpu-uuid "$uuid" --deadline "$deadline"
exit_code=$?
printf '%s\n' "$exit_code" > "$shard/exit_code.txt"
date -u +%FT%TZ > "$shard/completed_utc.txt"
exit "$exit_code"
