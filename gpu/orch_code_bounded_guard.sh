#!/bin/bash
set -euo pipefail
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
printf '%s\n' "$((started + 1740))" > "$launch/deadline_epoch.txt"
date -u +%FT%TZ > "$launch/started_utc.txt"
export PYTHONPATH="$source_dir" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1
clear=false
for attempt in 1 2 3; do
    if timeout 30 env CUDA_VISIBLE_DEVICES= python3 "$scanner" "$index" "$uuid" < "$services" > "$launch/resource_${attempt}.json"; then
        clear=true
        break
    fi
    sleep 2
done
test "$clear" = true
export CUDA_VISIBLE_DEVICES="$uuid"
set +e
timeout --signal=INT --kill-after=30 1680 "$runtime" -B -m gpu.orch_code_bounded_screen \
    --phase screen --bundle /tmp/astra_portable_37ec_20260914_attempt1 --model-dir "$model" \
    --tasks "$source_dir/research_notes/analysis/orch_code_bounded_20260914_attempt1/TASKS.json" \
    --output "$root/shard${index}" --shard "$index" --gpu-uuid "$uuid"
status="$?"
set -e
printf '%s\n' "$status" > "$launch/exit_code.txt"
date -u +%FT%TZ > "$launch/finished_utc.txt"
exit "$status"
