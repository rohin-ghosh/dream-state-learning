#!/bin/bash
# fires when RP lives have produced their first two parent_brief.json (ritual check at sleep)
S2="/Users/rohing/dream-state/gpu/ovx_ssh.sh"; S1="/Users/rohing/dream-state/gpu/a40_ssh.sh"
for ((i=0; i<40; i++)); do
  n2=$(bash "$S2" 'ls ~/v6_out/RP_B_seed*/sleep_*/parent_brief.json 2>/dev/null | wc -l' 2>/dev/null)
  n1=$(bash "$S1" 'ls ~/v6_out/RP_B_seed*/sleep_*/parent_brief.json 2>/dev/null | wc -l' 2>/dev/null)
  echo "$(date '+%H:%M') rp_briefs n2=$n2 n1=$n1"
  if [ "${n2:-0}" -ge 2 ] || [ "${n1:-0}" -ge 1 -a "${n2:-0}" -ge 1 ]; then echo "RP_FIRST_BRIEFS:n2=$n2 n1=$n1"; exit 0; fi
  sleep 900
done
echo RP_WATCH_WINDOW_DONE
