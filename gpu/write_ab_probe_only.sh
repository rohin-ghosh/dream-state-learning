#!/bin/bash
# Probe-only pass for the write pretest (gpu/write_ab.sh): probes the adapters that already have a DONE marker
# plus OFF and the mid-life brief, with the runbook's exact settings, and leaves the runbook's step markers so a
# still-running write_ab.sh chain skips those probes instead of repeating them.
# Usage (on a node, from ~/dream-state): bash gpu/write_ab_probe_only.sh <gpu> <life_dir> [cells=A,A_v3,B,C] [sleep_ep=512]
set -u
G="${1:?gpu}"; LIFE="${2:?life dir}"; CELLS="${3:-A,A_v3,B,C}"; SLEEP_EP="${4:-512}"
cd ~/dream-state || exit 1
export HF_HUB_OFFLINE=1 CUDA_HOME=/usr/local/cuda-13.0 PATH=/usr/local/cuda-13.0/bin:$HOME/v2/venv/bin:$PATH
P=~/v2/venv/bin/python; LIFE="${LIFE%/}"; L=$(basename "$LIFE")
OUT="${WRITE_AB_OUT:-$HOME/v6_out/pretest_write_ab}/$L"
REPS="${WRITE_AB_REPS:-2}"; GEN_SEED="${WRITE_AB_GEN_SEED:-4242}"; BUDGET="${WRITE_AB_BUDGET:-16}"
PANEL="$OUT/panel_v1.json"; SLEEP=$(printf "%s/sleep_%04d" "$LIFE" "$SLEEP_EP")
mkdir -p "$OUT/probes" "$OUT/markers"
probe() { # tag adapter(optional) panel(optional) brief(optional)
  local tag="$1" ad="$2" pn="$3" bf="${4:-}"; local o="$OUT/probes/$tag.json"
  if [ -f "$OUT/markers/probe_$tag" ] || [ -f "$o" ]; then echo "[probe_only] skip $tag"; return 0; fi
  local args=(--out "$o" --reps "$REPS" --gen-seed "$GEN_SEED" --budget-ticks "$BUDGET")
  [ -n "$ad" ] && args+=(--adapter "$ad"); [ -n "$pn" ] && args+=(--panel "$pn"); [ -n "$bf" ] && args+=(--brief-file "$bf")
  local t0=$(date +%s)
  CUDA_VISIBLE_DEVICES=$G $P -m organism_v6.probe_adapter "${args[@]}" > "$OUT/probe_$tag.out" 2>&1; local rc=$?
  local dt=$(( $(date +%s) - t0 ))
  echo "{\"step\": \"probe_$tag\", \"seconds\": $dt, \"rc\": $rc, \"by\": \"probe_only\"}" >> "$OUT/timings.jsonl"
  if [ $rc -ne 0 ]; then echo "[probe_only] FAIL probe_$tag rc=$rc"; tail -5 "$OUT/probe_$tag.out"; return $rc; fi
  touch "$OUT/markers/probe_$tag"; echo "[probe_only] done probe_$tag in ${dt}s: $(grep -o 'PROBE_DONE.*' "$OUT/probe_$tag.out" | head -1)"
}
IFS=',' read -ra CELL_ARR <<< "$CELLS"
for C in "${CELL_ARR[@]}"; do
  AD="$OUT/adapters/$C"; [ -f "$AD/DONE" ] || { echo "[probe_only] no adapter for $C (skipped)"; continue; }
  probe "${C}_report" "$AD" ""; probe "${C}_disjoint" "$AD" "$PANEL"
done
probe OFF_report "" ""; probe OFF_disjoint "" "$PANEL"
if [ -f "$SLEEP/waking_brief.txt" ]; then
  BF="$SLEEP/waking_brief.txt"; [ -f "$SLEEP/parent_brief.txt" ] && BF="$BF,$SLEEP/parent_brief.txt"
  probe brief_mid_report "" "" "$BF"; probe brief_mid_disjoint "" "$PANEL" "$BF"
else echo "[probe_only] brief_mid MISSING: no $SLEEP/waking_brief.txt"; fi
echo "[probe_only] PROBE_ONLY_DONE cells=$CELLS"
