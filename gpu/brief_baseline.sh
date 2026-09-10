#!/bin/bash
# Review M4: the equally-capable TEXT-MEMORY agent as a baseline (brief-only proxy).
# For every finished life on this node: frozen model + the life's FINAL waking brief (+ parent brief
# for RP/R4), NO adapter, probed on the 8 report programs and on disjoint panel v1, 2 seeded reps each.
# Compare with the same life's adapter ON (life probes / disjoint re-probe) and adapter OFF.
# Usage (on a node): bash gpu/brief_baseline.sh <gpu>
G="${1:?gpu}"; cd ~/dream-state
export HF_HUB_OFFLINE=1 CUDA_HOME=/usr/local/cuda-13.0 PATH=/usr/local/cuda-13.0/bin:$HOME/v2/venv/bin:$PATH
P=~/v2/venv/bin/python; OUT=~/v6_out/brief_baseline; mkdir -p $OUT; PANEL=~/v6_out/disjoint_panel/panel_v1.json; SEED=4242
for d in ~/v6_out/R2_B_seed* ~/v6_out/RP_B_seed* ~/v6_out/R3_B_seed* ~/v6_out/R4_B_seed*; do
  [ -d "$d" ] || continue; L=$(basename "$d")
  # finished = LIFE_DONE marker, or all 32 sleeps present (RP_B_seed402 ended without the marker)
  [ -f "$d/LIFE_DONE" ] || [ -d "$d/sleep_1024" ] || continue
  last=$(ls -d $d/sleep_*/ 2>/dev/null | while read s; do [ -f "$s/waking_brief.txt" ] && echo "$s"; done | sort | tail -1)
  [ -n "$last" ] || continue
  bf="$last/waking_brief.txt"
  pb=$(ls -d $d/sleep_*/parent_brief.txt 2>/dev/null | sort | tail -1)
  files="$bf"; [ -n "$pb" ] && files="$bf,$pb"
  for tag in report disjoint; do
    o="$OUT/${L}_brief_${tag}.json"; [ -f "$o" ] && { echo "skip $o"; continue; }
    if [ $tag = report ]; then CUDA_VISIBLE_DEVICES=$G $P -m organism_v6.probe_adapter --out "$o" --reps 2 --gen-seed $SEED --brief-file "$files" > "$o.out" 2>&1
    else CUDA_VISIBLE_DEVICES=$G $P -m organism_v6.probe_adapter --out "$o" --reps 2 --gen-seed $SEED --panel "$PANEL" --brief-file "$files" > "$o.out" 2>&1; fi
    echo "done $L $tag: $(grep -o 'PROBE_DONE.*' "$o.out")"
  done
done
echo BRIEF_BASELINE_DONE
