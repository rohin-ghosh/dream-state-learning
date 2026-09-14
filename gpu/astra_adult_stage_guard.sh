#!/bin/bash
set -eu
sleep 3
campaign="$1"
source_dir="$2"
commit="$3"
index="$4"
uuid="$5"
arm="$6"
adapter="$7"
adapter_sha="$8"
stage="$9"
cycle="${10:-1}"
prior="${11:-}"
extra=(--cycle "$cycle")
readout_extra=()
if test "$cycle" = 2; then
    test -n "$prior"
    extra+=(--prior-adult-collection "$prior")
    readout_extra=(--reader-wrapper 0)
else
    test -z "$prior"
fi
root="$campaign/$arm"
case "$stage" in
    train) duration=7440 ;;
    before|after_w0|recollect|recollect_rehearsal|recollect_revision|recollect_base_diagnostic) duration=1920 ;;
    *) exit 2 ;;
esac
if test "$stage" = recollect_revision || test "$stage" = recollect_base_diagnostic; then
    test -f "$root/recollect_rehearsal/RESULT.json"
    test -f "$root/recollect_rehearsal/SLEEP_NOTE.json"
    test ! -e "$root/$stage"
fi
if test "$stage" = recollect_base_diagnostic; then
    test -f "$root/recollect_revision/RESULT.json"
    test -f "$root/recollect_revision/SLEEP_NOTE.json"
fi
mkdir "$root/launch_$stage"
clear=false
for attempt in 1 2 3 4 5 6; do
    if timeout 30 env CUDA_VISIBLE_DEVICES= python3 /tmp/astra_cue_sensitivity_20260914_attempt1/scanner.py "$index" "$uuid" < /tmp/astra_stage2a_reduced_20260914_attempt1/service_exceptions.json > "$root/launch_$stage/resource_${attempt}.json"; then
        clear=true
        break
    fi
    sleep 5
done
if test "$clear" != true; then
    date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch_$stage/GUARD_ABORT.txt"
    exit 1
fi
python3 -c 'import sys,time; assert time.time()+int(sys.argv[1]) < 1789980180-21600' "$duration"
printf '%s\n' "$$" > "$root/launch_$stage/guardian_pid.txt"
printf '%s\n' "$commit" > "$root/launch_$stage/source_commit.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch_$stage/started_utc.txt"
export PYTHONPATH="$source_dir" CUDA_VISIBLE_DEVICES="$uuid" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
python=/localhome/local-rohing/v2/venv/bin/python
common=("${extra[@]}" --development-arm "$arm" --initial-adapter-dir "$adapter" --expected-initial-adapter-sha256 "$adapter_sha" --gpu-uuid "$uuid"
    --model-dir /localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28
    --expected-base-sha256 a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992
    --collection /tmp/astra_microloop_20260914_attempt2/collection
    --cue-collection /tmp/astra_cue_lastturn_20260914_attempt1/run --adult-collection "$root/collect")
if test "$stage" = recollect_base_diagnostic; then
    timeout --signal=INT --kill-after=60 1860 "$python" -B -m gpu.astra_experienced_event_adult_cycle "${common[@]}" --phase recollect_base_diagnostic --previous-recollection "$root/recollect_rehearsal" --output "$root/recollect_base_diagnostic"
elif test "$stage" = recollect_revision; then
    timeout --signal=INT --kill-after=60 1860 "$python" -B -m gpu.astra_experienced_event_adult_cycle "${common[@]}" --phase recollect_revision --sleep-recipe parental_revision_v1 --previous-recollection "$root/recollect_rehearsal" --output "$root/recollect_revision"
elif test "$stage" = recollect_rehearsal; then
    timeout --signal=INT --kill-after=60 1860 "$python" -B -m gpu.astra_experienced_event_adult_cycle "${common[@]}" --phase recollect --sleep-recipe rehearsal_allowed_v2 --output "$root/recollect_rehearsal"
elif test "$stage" = recollect; then
    timeout --signal=INT --kill-after=60 1860 "$python" -B -m gpu.astra_experienced_event_adult_cycle "${common[@]}" --phase recollect --output "$root/recollect"
elif test "$stage" = after_w0; then
    timeout --signal=INT --kill-after=60 1860 "$python" -B -m gpu.astra_experienced_event_adult_cycle "${common[@]}" --phase readout --state AFTER --reader-wrapper 0 --adapter-dir "$root/train/adapter" --output "$root/after_w0_reader"
elif test "$stage" = train; then
    timeout --signal=INT --kill-after=60 5460 "$python" -B -m gpu.astra_experienced_event_adult_cycle "${common[@]}" --phase train --output "$root/train"
    timeout --signal=INT --kill-after=60 1860 "$python" -B -m gpu.astra_experienced_event_adult_cycle "${common[@]}" "${readout_extra[@]}" --phase readout --state AFTER --adapter-dir "$root/train/adapter" --output "$root/after"
else
    timeout --signal=INT --kill-after=60 1860 "$python" -B -m gpu.astra_experienced_event_adult_cycle "${common[@]}" "${readout_extra[@]}" --phase readout --state BEFORE --output "$root/before"
fi
date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch_$stage/completed_utc.txt"
