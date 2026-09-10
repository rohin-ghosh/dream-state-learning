#!/bin/bash
S2="/Users/rohing/dream-state/gpu/ovx_ssh.sh"; S1="/Users/rohing/dream-state/gpu/a40_ssh.sh"
G='grep -oE "LINEAGE_[a-z]+_r[0-9]_[a-z]+_FAILED_s[0-9]+|LINEAGE3_DONE_[a-z]+_s[0-9]+" | sort -u | tr "\n" ","'
for ((i=0; i<90; i++)); do
  O2=$(bash "$S2" "l=\$(cat ~/v6_out/lineage3_*_s800[34].out 2>/dev/null | $G); echo \"lin2=\$l\"" 2>/dev/null)
  O1=$(bash "$S1" "l=\$(cat ~/v6_out/lineage3_self_s8001.out 2>/dev/null | $G); q=\$(ls ~/v6_out/R2_B_seed0/probe_ep0256.json ~/v6_out/R2_B_seed[01]/probe_ep0320.json 2>/dev/null | wc -l); echo \"lin1=\$l probes=\$q\"" 2>/dev/null)
  echo "$(date '+%H:%M') $O2 $O1"
  case "$O2 $O1" in *FAILED*) echo "WATCH13_FAILURE:$O2 $O1"; exit 0 ;; esac
  d=$(echo "$O2 $O1" | grep -o "LINEAGE3_DONE" | wc -l)
  if [ "$d" -ge 4 ]; then echo "ALL_LINEAGES_DONE:$O2 $O1"; exit 0; fi
  if [ "$d" -ge 2 ]; then echo "MORE_LINEAGES_DONE:$O2 $O1"; exit 0; fi
  sleep 900
done
echo WATCH13_WINDOW_DONE
