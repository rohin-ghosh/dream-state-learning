#!/bin/bash
set -euo pipefail
test "$#" -eq 10
root="$1"
source_dir="$2"
commit="$3"
index="$4"
uuid="$5"
arm="$6"
scanner="$7"
exceptions="$8"
lease_end="$9"
python="${10}"
case "$index:$arm:$uuid" in
    4:RICH:GPU-31583768-d90f-520c-51ed-5dac761526d0) ;;
    5:TERSE:GPU-c1650c7f-ac26-f1a0-2ab8-c7354a6f27c9) ;;
    *) exit 2 ;;
esac
test "$(cat "$root/source_commit.txt")" = "$commit"
test -f "$root/preGPU_publication.txt"
test -f "$root/source.tar.gz"
sha256sum -c "$root/source.sha256"
tar --compare -f "$root/source.tar.gz" -C "$source_dir"
mkdir "$root/launch_$arm"
launch="$root/launch_$arm"
trap 'printf "%s\n" "$?" > "$launch/exit_code.txt"; date -u +%FT%TZ > "$launch/finished_utc.txt"' EXIT
started=$(date +%s)
deadline=$(( started + 1800 ))
test "$deadline" -lt "$(( lease_end - 21600 ))"
printf '%s\n' "$$" > "$launch/guardian_pid.txt"
printf '%s\n' "$deadline" > "$launch/deadline_epoch.txt"
printf '%s\n' "$lease_end" > "$launch/lease_end_epoch.txt"
date -u +%FT%TZ > "$launch/started_utc.txt"
export PYTHONPATH="$source_dir" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1
env CUDA_VISIBLE_DEVICES= timeout 30 python3 "$scanner" "$index" "$uuid" < "$exceptions" > "$launch/admission.json"
env CUDA_VISIBLE_DEVICES= python3 - "$root/prepare_$arm/RESULT.json" "$source_dir" "$commit" "$index" "$uuid" <<'PY'
import json
from pathlib import Path
import subprocess
import sys
from gpu import orch_persist_code_screen as driver
from gpu import astra_experienced_event_microloop as source
result = json.loads(Path(sys.argv[1]).read_text())
assert result['status'] == 'PREPARED_NO_MODEL' and result['model_calls'] == 0
assert result['binding']['source_commit'] == sys.argv[3]
assert result['binding']['driver_sha256'] == source.file_hash(driver.__file__)
assert result['binding']['helper_sha256'] == source.file_hash(driver.ledger.__file__)
assert result['binding']['protocol_sha256'] == source.file_hash(Path(sys.argv[2]) / driver.PROTOCOL)
lines = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid', '--format=csv,noheader'], text=True).splitlines()
assert any(line.replace(' ', '') == sys.argv[4]+','+sys.argv[5] for line in lines)
PY
remaining=$(( deadline - 60 - $(date +%s) ))
test "$remaining" -gt 0
model=/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28
env CUDA_VISIBLE_DEVICES="$uuid" timeout --signal=INT --kill-after=30 "$remaining" "$python" -B -m gpu.orch_persist_code_screen \
    --bundle /tmp/astra_portable_37ec_20260914_attempt1 --model-dir "$model" \
    --output "$root/$arm" --source-commit "$commit" --arm "$arm" --gpu-uuid "$uuid" --deadline-epoch "$(( deadline - 60 ))"
env CUDA_VISIBLE_DEVICES= timeout 30 python3 "$scanner" "$index" "$uuid" < "$exceptions" > "$launch/release.json"
