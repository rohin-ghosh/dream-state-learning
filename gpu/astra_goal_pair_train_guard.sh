#!/bin/bash
set -eu
test "$#" -eq 6
root="$1"
source_dir="$2"
commit="$3"
index="$4"
uuid="$5"
arm="$6"
case "$arm" in FULL_TARGET|NEW_TRAJECTORY_LOSS_OFF) ;; *) exit 2 ;; esac
admission_started=$(date +%s)
deadline=$(( admission_started + 11220 ))
test "$(cat "$root/source_commit.txt")" = "$commit"
test -f "$root/prepare/RESULT.json"
test ! -e "$root/prepare/FAILED.json"
test ! -e "$root/$arm"
python3 -c 'import hashlib,json,sys; r=json.load(open(sys.argv[1])); assert r["schema"] == "DEV_GOAL_PAIR_INCREMENTAL_FIT_V1" and r["phase"] == "prepare" and r["status"] == "PREPARED_NO_MODEL" and r["new_actual_train_targets"] == 48 and r["probe_training_rows"] == 0; assert r["entry_sha256"] == hashlib.sha256(open(sys.argv[2],"rb").read()).hexdigest()' "$root/prepare/RESULT.json" "$source_dir/gpu/astra_goal_pair_train.py"
python3 -c 'import time; assert time.time()+11220 < 1789980180-21600'
mkdir "$root/$arm"
launch="$root/$arm/launch"
mkdir "$launch"
clear=false
for attempt in 1 2 3 4 5 6; do
    if timeout 30 env CUDA_VISIBLE_DEVICES= python3 /tmp/astra_cue_sensitivity_20260914_attempt1/scanner.py "$index" "$uuid" < /tmp/astra_stage2a_reduced_20260914_attempt1/service_exceptions.json > "$launch/resource_${attempt}.json"; then
        clear=true
        break
    fi
    sleep 5
done
if test "$clear" != true || test "$(( $(date +%s) - admission_started ))" -gt 300; then
    date -u +%Y-%m-%dT%H:%M:%SZ > "$launch/GUARD_ABORT.txt"
    exit 1
fi
printf '%s\n' "$$" > "$launch/guardian_pid.txt"
printf '%s\n' "$commit" > "$launch/source_commit.txt"
printf '%s\n' "$deadline" > "$launch/deadline_epoch.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$launch/started_utc.txt"
export PYTHONPATH="$source_dir" CUDA_VISIBLE_DEVICES="$uuid" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
common=(--base-after /tmp/astra_adult_cycle2_20260914_attempt1/CUE_REPLAY/corrective_sleep/CHILD_CORRECTIVE/after
    --campaign /tmp/astra_reader_audit_lesson_20260914_attempt1
    --audit-root /tmp/astra_actual_reader_audit_20260914_attempt1
    --repair-root /tmp/astra_selected_reader_repair_20260914_attempt1
    --cycle-root /tmp/astra_fresh_reader_cycle_20260914_attempt2
    --lesson-root /tmp/astra_event_two_hop_lesson_20260914_attempt1
    --transfer-root /tmp/astra_event_two_hop_transfer_20260914_attempt2
    --collection-root /tmp/astra_goal_pair_collection_20260914_attempt1 --gpu-uuid "$uuid" --arm "$arm")
run_stage() {
    seconds="$1"
    shift
    remaining=$(( deadline - $(date +%s) - 60 ))
    test "$remaining" -gt 0
    if test "$seconds" -gt "$remaining"; then seconds="$remaining"; fi
    timeout --signal=INT --kill-after=60 "$seconds" /localhome/local-rohing/v2/venv/bin/python -B -m gpu.astra_goal_pair_train "${common[@]}" "$@"
}
run_stage 7200 --phase train --output "$root/$arm/train"
run_stage 3600 --phase after --training "$root/$arm/train" --output "$root/$arm/after"
date -u +%Y-%m-%dT%H:%M:%SZ > "$launch/completed_utc.txt"
