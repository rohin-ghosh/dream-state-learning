#!/bin/bash
set -eu
test "$#" -eq 5
root="$1"
source_dir="$2"
commit="$3"
index="$4"
uuid="$5"
test -f "$root/prepare/RESULT.json"
test ! -e "$root/prepare/FAILED.json"
test "$(cat "$root/source_commit.txt")" = "$commit"
test ! -e "$root/expose"
test ! -e "$root/teach"
test ! -e "$root/baseline"
python3 -c 'import hashlib,json,sys; r=json.load(open(sys.argv[1])); assert r["schema"] == "DEV_GOAL_PAIR_COLLECTION_V1" and r["phase"] == "prepare" and r["status"] == "PREPARED_NO_MODEL"; assert r["entry_sha256"] == hashlib.sha256(open(sys.argv[2],"rb").read()).hexdigest()' "$root/prepare/RESULT.json" "$source_dir/gpu/astra_goal_pair_collection.py"
python3 -c 'import time; assert time.time()+6060 < 1789980180-21600'
deadline=$(( $(date +%s) + 6060 ))
mkdir "$root/launch"
clear=false
for attempt in 1 2 3 4 5 6; do
    if timeout 30 env CUDA_VISIBLE_DEVICES= python3 /tmp/astra_cue_sensitivity_20260914_attempt1/scanner.py "$index" "$uuid" < /tmp/astra_stage2a_reduced_20260914_attempt1/service_exceptions.json > "$root/launch/resource_${attempt}.json"; then
        clear=true
        break
    fi
    sleep 5
done
if test "$clear" != true; then
    date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch/GUARD_ABORT.txt"
    exit 1
fi
printf '%s\n' "$$" > "$root/launch/guardian_pid.txt"
printf '%s\n' "$commit" > "$root/launch/source_commit.txt"
printf '%s\n' "$deadline" > "$root/launch/deadline_epoch.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch/started_utc.txt"
export PYTHONPATH="$source_dir" CUDA_VISIBLE_DEVICES="$uuid" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
common=(--base-after /tmp/astra_adult_cycle2_20260914_attempt1/CUE_REPLAY/corrective_sleep/CHILD_CORRECTIVE/after
    --campaign /tmp/astra_reader_audit_lesson_20260914_attempt1
    --audit-root /tmp/astra_actual_reader_audit_20260914_attempt1
    --repair-root /tmp/astra_selected_reader_repair_20260914_attempt1
    --cycle-root /tmp/astra_fresh_reader_cycle_20260914_attempt2
    --lesson-root /tmp/astra_event_two_hop_lesson_20260914_attempt1
    --transfer-root /tmp/astra_event_two_hop_transfer_20260914_attempt2 --gpu-uuid "$uuid")
run_stage() {
    remaining=$(( deadline - $(date +%s) - 60 ))
    test "$remaining" -gt 0
    seconds=1860
    if test "$seconds" -gt "$remaining"; then seconds="$remaining"; fi
    timeout --signal=INT --kill-after=60 "$seconds" /localhome/local-rohing/v2/venv/bin/python -B -m gpu.astra_goal_pair_collection "${common[@]}" "$@"
}
run_stage --phase expose --output "$root/expose"
python3 -c 'import json,sys; r=json.load(open(sys.argv[1])); assert r["status"] == "COMPLETE" and r["source_ready"] is True' "$root/expose/RESULT.json"
run_stage --phase teach --exposure "$root/expose" --output "$root/teach"
run_stage --phase baseline --exposure "$root/expose" --teaching "$root/teach" --output "$root/baseline"
date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch/completed_utc.txt"
