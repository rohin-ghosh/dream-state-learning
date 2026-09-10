#!/bin/bash
S2="/Users/rohing/dream-state/gpu/ovx_ssh.sh"; S1="/Users/rohing/dream-state/gpu/a40_ssh.sh"
C='c=""; for d in ~/v6_out/R2_B_seed* ~/v6_out/RP_B_seed* ~/v6_out/R3_B_seed* ~/v6_out/R_B_seed0; do [ -d "$d" ] || continue; L=$(basename $d); test -f $d/LIFE_DONE && continue; pgrep -f "life-dir.*/$L( |$)" >/dev/null || c="$c $L"; done; iv=$(grep -l "\"intervened\": true" ~/v6_out/RP_B_seed40[02]/sleep_*/parent_brief.json 2>/dev/null | wc -l); g=$(ls ~/v6_out/R3_B_seed*/sleep_*/gate.json 2>/dev/null | wc -l); s=$(test -f ~/v6_out/RP_B_seed401/sleep_0320/parent_brief.json && echo 1 || echo 0); echo "lives=$(pgrep -c -f "[r]un_life_v2 ") iv0402=$iv gates=$g s401_320=$s crash=$c"'
for ((i=0; i<48; i++)); do
  O1=$(bash "$S1" "$C" 2>/dev/null); O2=$(bash "$S2" "$C" 2>/dev/null)
  echo "$(date '+%H:%M') n1[$O1] n2[$O2]"
  for O in "$O1" "$O2"; do case "$O" in *crash=\ *[A-Za-z]*) echo "LIFE_CRASHED: n1[$O1] n2[$O2]"; exit 0 ;; esac; done
  case "$O1" in *gates=[2-9]*) echo "R3_SECOND_GATE: n1[$O1] n2[$O2]"; exit 0 ;; esac
  case "$O1 $O2" in *iv0402=[1-9]*) echo "RP_400_OR_402_INTERVENED: n1[$O1] n2[$O2]"; exit 0 ;; esac
  case "$O2" in *s401_320=1*) echo "RP_401_SLEEP320: n1[$O1] n2[$O2]"; exit 0 ;; esac
  sleep 1800
done
echo ONE_WATCH4_WINDOW_DONE
