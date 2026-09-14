#!/bin/bash
set -euo pipefail
test "$#" -eq 8
root="$1"
source_dir="$2"
index="$3"
uuid="$4"
shard="$5"
lease_end="$6"
archive_sha="$7"
batch_deadline="$8"
case "$index:$shard" in 4:0|5:1|6:2|7:3) ;; *) exit 2 ;; esac
scanner=/tmp/astra_cue_sensitivity_20260914_attempt1/scanner.py
services=/tmp/astra_stage2a_reduced_20260914_attempt1/service_exceptions.json
runtime=/localhome/local-rohing/v2/venv/bin/python
model=/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28
bundle=/tmp/astra_portable_37ec_20260914_attempt1
bundle_sha=5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469
started=$(date +%s)
test "$batch_deadline" -le "$((started + 2700))"
test "$batch_deadline" -lt "$((lease_end - 21600))"
test "$(sha256sum "$root/source.tar" | cut -d' ' -f1)" = "$archive_sha"
python3 "$source_dir/gpu/orch_math_rich_source.py" "$root/source.tar" "$source_dir"
test "$(sha256sum "$scanner" | cut -d' ' -f1)" = 6ed5c48c144dcf26dcb856798ab31d69e39bc66b6780211f2b10553972f8519b
test "$(sha256sum "$services" | cut -d' ' -f1)" = ed2c9111a50b09bdf20859d3395769945b79ce8ba1f5554ed7fe55b99cfd5117
test "$(nvidia-smi -i "$index" --query-gpu=uuid --format=csv,noheader)" = "$uuid"
launch="$root/shard${shard}_launch"
mkdir "$launch"
printf '%s\n' "$$" > "$launch/guardian_pid.txt"
printf '%s\n' "$lease_end" > "$launch/lease_end_epoch.txt"
printf '%s\n' "$batch_deadline" > "$launch/deadline_epoch.txt"
printf '%s\n' "$archive_sha" > "$launch/source_archive_sha256.txt"
date -u +%FT%TZ > "$launch/started_utc.txt"
export PYTHONPATH="$source_dir" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1
python3 - "$root/prepare/RESULT.json" "$root/TASKS.json" <<'PY'
import hashlib
import json
import sys
from pathlib import Path
from gpu import orch_math_record_screen as screen
from organism_v6 import orch_math_record as policy
result = json.load(open(sys.argv[1]))
assert result['status'] == 'PREPARED_NO_MODEL' and result['model_calls'] == 0
assert result['base_verification']['verified']
assert result['driver_sha256'] == hashlib.sha256(Path(screen.__file__).read_bytes()).hexdigest()
assert result['policy_sha256'] == hashlib.sha256(Path(policy.__file__).read_bytes()).hexdigest()
assert result['tasks_sha256'] == hashlib.sha256(Path(sys.argv[2]).read_bytes()).hexdigest()
PY
clear=false
for attempt in 1 2 3 4 5 6; do
    if timeout 30 env CUDA_VISIBLE_DEVICES= python3 "$scanner" "$index" "$uuid" < "$services" > "$launch/resource_${attempt}.json"; then
        clear=true
        break
    fi
    sleep 2
done
test "$clear" = true
remaining="$((batch_deadline - $(date +%s) - 60))"
test "$remaining" -gt 0
export CUDA_VISIBLE_DEVICES="$uuid"
set +e
timeout --signal=INT --kill-after=60 "$remaining" "$runtime" -B -m gpu.orch_math_record_screen \
    --phase screen --bundle "$bundle" --bundle-sha "$bundle_sha" --model-dir "$model" \
    --tasks "$root/TASKS.json" --output "$root/shard${shard}" --shard "$shard" --gpu-uuid "$uuid" \
    --deadline "$((batch_deadline - 60))"
status="$?"
set -e
printf '%s\n' "$status" > "$launch/exit_code.txt"
date -u +%FT%TZ > "$launch/finished_utc.txt"
nvidia-smi -i "$index" --query-gpu=index,uuid,memory.used,utilization.gpu --format=csv,noheader > "$launch/final_gpu.txt"
exit "$status"
