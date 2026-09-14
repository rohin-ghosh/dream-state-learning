#!/bin/bash
set -euo pipefail
test "$#" -eq 12
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
bundle="${11}"
model_dir="${12}"
case "$index:$arm" in
    6:RICH|7:TERSE) ;;
    *) exit 2 ;;
esac
started=$(date +%s)
deadline=$(( started + 2700 ))
test "$deadline" -lt "$(( lease_end - 21600 ))"
test "$(cat "$root/source_commit.txt")" = "$commit"
test -x "$python"
test -f "$scanner"
test -f "$exceptions"
mkdir "$root/$arm-launch"
launch="$root/$arm-launch"
trap 'printf "%s\n" "$?" > "$launch/exit_code.txt"; date -u +%Y-%m-%dT%H:%M:%SZ > "$launch/finished_utc.txt"' EXIT
export PYTHONPATH="$source_dir" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1
env CUDA_VISIBLE_DEVICES= python3 - "$root/prepare-$arm/RESULT.json" <<'PY'
import json
import sys
from gpu import orch_persist_math_screen as driver
result = json.load(open(sys.argv[1]))
assert result['status'] == 'PREPARED_NO_MODEL'
assert result['model_calls'] == result['fits'] == result['updates'] == 0
assert result['helpers'] == driver.helpers()
assert result['base_verification']['verified'] is True
assert result['bundle_manifest_sha256'] == driver.BUNDLE_SHA
PY
printf '%s\n' "$$" > "$launch/guardian_pid.txt"
printf '%s\n' "$deadline" > "$launch/deadline_epoch.txt"
printf '%s\n' "$lease_end" > "$launch/actual_lease_end_epoch.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$launch/started_utc.txt"
env CUDA_VISIBLE_DEVICES= timeout 30 python3 "$scanner" "$index" "$uuid" < "$exceptions" > "$launch/resource_before.json"
test "$(nvidia-smi --query-gpu=index,uuid --format=csv,noheader | awk -F', ' -v selected="$index" '$1==selected {print $2}')" = "$uuid"
remaining=$(( deadline - $(date +%s) - 60 ))
test "$remaining" -gt 0
set +e
env CUDA_VISIBLE_DEVICES="$uuid" timeout --signal=INT --kill-after=60 "$remaining" "$python" -B -m gpu.orch_persist_math_screen \
    --bundle "$bundle" --model-dir "$model_dir" --output "$root/$arm" --phase screen --arm "$arm" \
    --gpu-uuid "$uuid" --deadline-epoch "$(( deadline - 60 ))"
native_status=$?
set -e
printf '%s\n' "$native_status" > "$launch/native_exit_code.txt"
env CUDA_VISIBLE_DEVICES= timeout 30 python3 "$scanner" "$index" "$uuid" < "$exceptions" > "$launch/resource_after.json"
exit "$native_status"
