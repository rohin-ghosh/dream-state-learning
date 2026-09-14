#!/bin/bash
set -euo pipefail
test "$#" -eq 5
root="$1"
index="$2"
uuid="$3"
source_sha="$4"
publication="$5"
shard="$root/shard$index"
test ! -e "$shard"
mkdir "$shard"
started=$(date +%s)
deadline=$(( started + 2400 ))
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
test "$(sha256sum /tmp/astra_rich_collection_20260914_attempt1/scanner.py | cut -d' ' -f1)" = "$(cat "$root/scanner_sha256.txt")"
test "$(sha256sum /tmp/astra_rich_collection_20260914_attempt1/service_exceptions.json | cut -d' ' -f1)" = "$(cat "$root/service_exceptions_sha256.txt")"
clear=false
for attempt in 1 2 3 4 5 6; do
    if timeout 30 env CUDA_VISIBLE_DEVICES= python3 /tmp/astra_rich_collection_20260914_attempt1/scanner.py "$index" "$uuid" < /tmp/astra_rich_collection_20260914_attempt1/service_exceptions.json > "$shard/RESOURCE_${attempt}.json"; then
        clear=true
        break
    fi
    sleep 5
done
test "$clear" = true
printf '%s\n' "$$" > "$shard/guardian_pid.txt"
printf '%s\n' "$deadline" > "$shard/deadline_epoch.txt"
date -u +%FT%TZ > "$shard/started_utc.txt"
export CUDA_VISIBLE_DEVICES="$uuid"
remaining=$(( deadline - $(date +%s) - 60 ))
test "$remaining" -gt 0
set +e
timeout --signal=INT --kill-after=60 "$remaining" /localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_game_run \
    --phase screen --bank "$root/FROZEN_BANK.json" \
    --bundle /tmp/astra_portable_37ec_20260914_attempt1 \
    --model-dir /localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28 \
    --source-archive "$root/source.tar.gz" --source-sha "$source_sha" \
    --source-manifest "$root/source/SOURCE_MANIFEST.json" --output "$shard/screen" \
    --shard "$index" --gpu-uuid "$uuid" --deadline "$deadline"
exit_code=$?
printf '%s\n' "$exit_code" > "$shard/exit_code.txt"
date -u +%FT%TZ > "$shard/completed_utc.txt"
exit "$exit_code"
