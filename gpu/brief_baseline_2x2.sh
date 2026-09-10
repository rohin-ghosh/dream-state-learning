#!/bin/bash
# Text-memory baseline, crossed cells (Astra memo 1, 2026-09-10): for every finished life on this node
#   A+B  = the life's FINAL committed adapter + its final waking brief (and parent brief for RP/R4)
#   F+R  = frozen model + a ROUTINE-ONLY brief (just the six-pass line), no adapter
# on both panels, 2 seeded reps. Together with brief_baseline.sh (F+B) and the life probes (A, F)
# this completes frozen/adapter x no-brief/own-brief, plus the recipe-transmission control.
# Usage (on a node): bash gpu/brief_baseline_2x2.sh <gpu>
G="${1:?gpu}"; cd ~/dream-state
export HF_HUB_OFFLINE=1 CUDA_HOME=/usr/local/cuda-13.0 PATH=/usr/local/cuda-13.0/bin:$HOME/v2/venv/bin:$PATH
P=~/v2/venv/bin/python; OUT=~/v6_out/brief_baseline; mkdir -p $OUT; PANEL=~/v6_out/disjoint_panel/panel_v1.json; SEED=4242
ROUTINE=$OUT/routine_only_brief.txt
[ -f "$ROUTINE" ] || printf -- '- **THEORY**: Initial passes (-mem2reg, -sroa, -gvn, -simplifycfg, -instcombine) consistently yield high reductions.\n' > "$ROUTINE"
run() { # tag out adapter(optional) brieffile panel(optional)
  local o="$1" ad="$2" bf="$3" pn="$4"; [ -f "$o" ] && { echo "skip $o"; return; }
  local args=(--out "$o" --reps 2 --gen-seed $SEED --brief-file "$bf"); [ -n "$ad" ] && args+=(--adapter "$ad"); [ -n "$pn" ] && args+=(--panel "$pn")
  CUDA_VISIBLE_DEVICES=$G $P -m organism_v6.probe_adapter "${args[@]}" > "$o.out" 2>&1
  echo "done $(basename $o): $(grep -o 'PROBE_DONE.*' "$o.out")"
}
for d in ~/v6_out/R2_B_seed* ~/v6_out/RP_B_seed* ~/v6_out/R3_B_seed* ~/v6_out/R4_B_seed*; do
  [ -d "$d" ] || continue; L=$(basename "$d")
  [ -f "$d/LIFE_DONE" ] || [ -d "$d/sleep_1024" ] || continue
  last=$(ls -d $d/sleep_*/ 2>/dev/null | while read s; do [ -f "$s/waking_brief.txt" ] && echo "$s"; done | sort | tail -1)
  [ -n "$last" ] || continue
  bf="$last/waking_brief.txt"; pb=$(ls -d $d/sleep_*/parent_brief.txt 2>/dev/null | sort | tail -1)
  files="$bf"; [ -n "$pb" ] && files="$bf,$pb"
  final=$(ls -d $d/sleep_*/adapter 2>/dev/null | while read a; do [ -f "$a/DONE" ] && echo "$a"; done | sort | tail -1)
  if [ -n "$final" ]; then
    run "$OUT/${L}_adapterbrief_report.json"   "$final" "$files" ""
    run "$OUT/${L}_adapterbrief_disjoint.json" "$final" "$files" "$PANEL"
  fi
  run "$OUT/${L}_routineonly_report.json"   "" "$ROUTINE" ""
  run "$OUT/${L}_routineonly_disjoint.json" "" "$ROUTINE" "$PANEL"
done
echo BRIEF_BASELINE_2X2_DONE
