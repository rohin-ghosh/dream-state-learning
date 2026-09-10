#!/bin/bash
# alerts when any R2/R life dir without LIFE_DONE has no running process, on either node
S2="/Users/rohing/dream-state/gpu/ovx_ssh.sh"; S1="/Users/rohing/dream-state/gpu/a40_ssh.sh"
CHK='c=""; for d in ~/v6_out/R2_B_seed* ~/v6_out/RP_B_seed* ~/v6_out/R_B_seed0; do [ -d "$d" ] || continue; L=$(basename $d); test -f $d/LIFE_DONE && continue; pgrep -f "life-dir.*/$L( |$)" >/dev/null || c="$c $L"; done; n=$(pgrep -c -f "[r]un_life_v2 "); s=$(ls -d ~/v6_out/R*_B_seed*/sleep_* 2>/dev/null | wc -l); echo "lives=$n sleeps_total=$s crash=$c"'
for ((i=0; i<96; i++)); do
  O1=$(bash "$S1" "$CHK" 2>/dev/null); O2=$(bash "$S2" "$CHK" 2>/dev/null)
  echo "$(date '+%H:%M') n1[$O1] n2[$O2]"
  for O in "$O1" "$O2"; do case "$O" in *crash=\ *[A-Za-z]*) echo "LIFE_CRASHED: n1[$O1] n2[$O2]"; exit 0 ;; esac; done
  sleep 900
done
echo LIVES_WATCH_WINDOW_DONE
