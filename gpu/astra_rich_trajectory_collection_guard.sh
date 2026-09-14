#!/bin/bash
set -eu
test "$#" -eq 12
root="$1"
source_dir="$2"
commit="$3"
index="$4"
uuid="$5"
shard="$6"
bundle="$7"
bundle_sha="$8"
model_dir="$9"
scanner="${10}"
service_exceptions="${11}"
lease_end_epoch="${12}"
case "$shard" in 0|1|2|3) ;; *) exit 2 ;; esac
admission_started=$(date +%s)
deadline=$(( admission_started + 15000 ))
test "$(cat "$root/source_commit.txt")" = "$commit"
test -f "$root/prepare/RESULT.json"
test ! -e "$root/prepare/FAILED.json"
for phase in expose teach critique baseline; do test ! -e "$root/$phase"; done
test -f "$scanner"
test -f "$service_exceptions"
python3 - "$root/prepare/RESULT.json" "$source_dir/gpu/astra_rich_trajectory_collection.py" "$shard" "$bundle" "$bundle_sha" "$model_dir" "$uuid" <<'PY'
import hashlib, json, sys
from pathlib import Path
result = json.loads(Path(sys.argv[1]).read_text())
assert result['schema'] == 'DEV_RICH_TRAJECTORY_COLLECTION_V1' and result['phase'] == 'prepare'
assert result['status'] == 'PREPARED_NO_MODEL' and result['expected_paired_targets'] == 96
assert result['shard'] == int(sys.argv[3]) and result['binding']['bundle_sha256'] == sys.argv[5]
assert result['entry_sha256'] == hashlib.sha256(Path(sys.argv[2]).read_bytes()).hexdigest()
assert Path(result['arguments']['bundle']).resolve() == Path(sys.argv[4]).resolve()
assert Path(result['arguments']['model_dir']).resolve() == Path(sys.argv[6]).resolve()
assert result['arguments']['gpu_uuid'] == sys.argv[7]
PY
python3 -c 'import sys,time; assert time.time()+15000 < int(sys.argv[1])-21600' "$lease_end_epoch"
mkdir "$root/launch"
clear=false
for attempt in 1 2 3 4 5 6; do
    if timeout 30 env CUDA_VISIBLE_DEVICES= python3 "$scanner" "$index" "$uuid" < "$service_exceptions" > "$root/launch/resource_${attempt}.json"; then
        clear=true
        break
    fi
    sleep 5
done
if test "$clear" != true || test "$(( $(date +%s) - admission_started ))" -gt 300; then
    date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch/GUARD_ABORT.txt"
    exit 1
fi
printf '%s\n' "$$" > "$root/launch/guardian_pid.txt"
printf '%s\n' "$commit" > "$root/launch/source_commit.txt"
printf '%s\n' "$deadline" > "$root/launch/deadline_epoch.txt"
printf '%s\n' "$lease_end_epoch" > "$root/launch/lease_end_epoch.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch/started_utc.txt"
export PYTHONPATH="$source_dir" CUDA_VISIBLE_DEVICES="$uuid" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
common=(--bundle "$bundle" --bundle-sha "$bundle_sha" --model-dir "$model_dir" --shard "$shard" --gpu-uuid "$uuid")
run_stage() {
    remaining=$(( deadline - $(date +%s) - 120 ))
    test "$remaining" -gt 0
    seconds=3600
    if test "$seconds" -gt "$remaining"; then seconds="$remaining"; fi
    timeout --signal=INT --kill-after=60 "$seconds" /localhome/local-rohing/v2/venv/bin/python -B -m gpu.astra_rich_trajectory_collection "${common[@]}" "$@"
}
run_stage --phase expose --output "$root/expose"
python3 -c 'import json,sys; r=json.load(open(sys.argv[1])); assert r["status"] == "COMPLETE" and r["source_ready"] is True' "$root/expose/RESULT.json"
run_stage --phase teach --exposure "$root/expose" --output "$root/teach"
run_stage --phase critique --exposure "$root/expose" --teaching "$root/teach" --output "$root/critique"
run_stage --phase baseline --exposure "$root/expose" --teaching "$root/teach" --critique "$root/critique" --output "$root/baseline"
date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch/completed_utc.txt"
