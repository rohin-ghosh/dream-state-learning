#!/bin/bash
# Review F1b: re-probe adapters on a panel DISJOINT from the gate/report panel.
# Usage (on a node): bash gpu/disjoint_reprobe.sh <gpu>
# Probes: base x3 reps (seeded), then for every finished/ongoing life on this node its final committed adapter
# and one mid-life committed adapter (nearest sleep_0512), 2 seeded reps each, on ~/v6_out/disjoint_panel/panel_v1.json.
G="${1:?gpu}"; cd ~/dream-state
export HF_HUB_OFFLINE=1 CUDA_HOME=/usr/local/cuda-13.0 PATH=/usr/local/cuda-13.0/bin:$HOME/v2/venv/bin:$PATH
P=~/v2/venv/bin/python; OUT=~/v6_out/disjoint_panel; PANEL=$OUT/panel_v1.json; SEED=4242
run() { # tag adapter reps
  local tag=$1 ad=$2 reps=$3
  [ -f "$OUT/$tag.json" ] && { echo "skip $tag"; return; }
  if [ -n "$ad" ]; then CUDA_VISIBLE_DEVICES=$G $P -m organism_v6.probe_adapter --out "$OUT/$tag.json" --adapter "$ad" --reps "$reps" --panel "$PANEL" --gen-seed $SEED > "$OUT/$tag.out" 2>&1
  else CUDA_VISIBLE_DEVICES=$G $P -m organism_v6.probe_adapter --out "$OUT/$tag.json" --reps "$reps" --panel "$PANEL" --gen-seed $SEED > "$OUT/$tag.out" 2>&1; fi
  echo "done $tag: $(grep -o 'PROBE_DONE.*' "$OUT/$tag.out")"
}
run base "" 3
for d in ~/v6_out/R2_B_seed* ~/v6_out/RP_B_seed* ~/v6_out/R3_B_seed* ~/v6_out/R4_B_seed*; do
  [ -d "$d" ] || continue; L=$(basename "$d")
  final=$(ls -d $d/sleep_*/adapter 2>/dev/null | while read a; do [ -f "$a/DONE" ] && echo "$a"; done | sort | tail -1)
  [ -n "$final" ] || continue
  run "${L}_final_$(basename $(dirname $final))" "$final" 2
  mid=$(ls -d $d/sleep_0[4-6]*/adapter 2>/dev/null | while read a; do [ -f "$a/DONE" ] && echo "$a"; done | sort | head -1)
  [ -n "$mid" ] && [ "$mid" != "$final" ] && run "${L}_mid_$(basename $(dirname $mid))" "$mid" 2
done
echo DISJOINT_REPROBE_DONE
