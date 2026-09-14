#!/bin/bash
set -euo pipefail
test "$#" -eq 4
root="$1"
index="$2"
uuid="$3"
archive_sha="$4"
case "$index" in 0|1|2|3) ;; *) exit 2 ;; esac
source_dir="$root/source"
runtime=/localhome/local-rohing/v2/venv/bin/python
model=/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28
scanner=/tmp/astra_cue_sensitivity_20260914_attempt1/scanner.py
services=/tmp/astra_stage2a_reduced_20260914_attempt1/service_exceptions.json
started=$(date +%s)
deadline="$((started + 1740))"
native_seconds=1560
resume_options=()
if test -f "$root/../shard${index}/FAILED.json"; then
    resume_options=(--resume-from "$root/../shard${index}")
    original_deadline=$(cat "$root/../shard${index}_launch/deadline_epoch.txt")
    deadline="$original_deadline"
    native_seconds="$((original_deadline - started - 90))"
    if test "$native_seconds" -gt 1560; then native_seconds=1560; fi
    test "$native_seconds" -gt 180
fi
lease_end=$(date -u -d '2026-09-21 08:43:00' +%s)
test "$((started + 1800))" -lt "$((lease_end - 21600))"
test "$(sha256sum "$root/source.tar" | cut -d' ' -f1)" = "$archive_sha"
python3 "$source_dir/gpu/orch_code_bounded_source.py" "$root/source.tar" "$source_dir"
test "$(sha256sum "$scanner" | cut -d' ' -f1)" = 6ed5c48c144dcf26dcb856798ab31d69e39bc66b6780211f2b10553972f8519b
test "$(sha256sum "$services" | cut -d' ' -f1)" = ed2c9111a50b09bdf20859d3395769945b79ce8ba1f5554ed7fe55b99cfd5117
test "$(nvidia-smi -i "$index" --query-gpu=uuid --format=csv,noheader)" = "$uuid"
launch="$root/shard${index}_launch"
mkdir "$launch"
printf '%s\n' "$$" > "$launch/guardian_pid.txt"
printf '%s\n' "$deadline" > "$launch/deadline_epoch.txt"
printf '%s\n' "$archive_sha" > "$launch/source_archive_sha256.txt"
date -u +%FT%TZ > "$launch/started_utc.txt"
export PYTHONPATH="$source_dir" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1
freeze="$source_dir/research_notes/analysis/orch_base_contract_20260914_attempt1/FREEZE.json"
python3 - "$root/prepare/RESULT.json" "$freeze" <<'PY'
import json
import sys
from gpu import orch_base_contract_screen as screen
from organism_v6 import orch_base_contract as policy
result = json.load(open(sys.argv[1]))
assert result['status'] == 'PREPARED_NO_MODEL' and result['model_calls'] == 0
assert result['base_verification']['verified']
assert result['driver_sha256'] == screen.digest(screen.__file__)
assert result['policy_sha256'] == screen.digest(policy.__file__)
assert result['freeze_sha256'] == screen.digest(sys.argv[2])
PY
timeout 30 env CUDA_VISIBLE_DEVICES= python3 "$scanner" "$index" "$uuid" < "$services" > "$launch/resource.json"
export CUDA_VISIBLE_DEVICES="$uuid"
set +e
timeout --signal=INT --kill-after=30 "$native_seconds" "$runtime" -B -m gpu.orch_base_contract_screen \
    --phase screen --bundle /tmp/astra_portable_37ec_20260914_attempt1 --model-dir "$model" \
    --freeze "$freeze" --output "$root/shard${index}" --shard "$index" --gpu-uuid "$uuid" "${resume_options[@]}"
status="$?"
set -e
printf '%s\n' "$status" > "$launch/exit_code.txt"
date -u +%FT%TZ > "$launch/finished_utc.txt"
exit "$status"
