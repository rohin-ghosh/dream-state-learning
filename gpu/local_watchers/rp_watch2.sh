#!/bin/bash
# fires on the first parent intervention in any RP life, or when RP lives reach sleep 128
S2="/Users/rohing/dream-state/gpu/ovx_ssh.sh"; S1="/Users/rohing/dream-state/gpu/a40_ssh.sh"
C='iv=$(grep -l "\"intervened\": true" ~/v6_out/RP_B_seed*/sleep_*/parent_brief.json 2>/dev/null | wc -l); s=$(ls -d ~/v6_out/RP_B_seed*/sleep_0128 2>/dev/null | wc -l); echo "iv=$iv s128=$s"'
for ((i=0; i<60; i++)); do
  O2=$(bash "$S2" "$C" 2>/dev/null); O1=$(bash "$S1" "$C" 2>/dev/null)
  echo "$(date '+%H:%M') n2[$O2] n1[$O1]"
  case "$O2 $O1" in *iv=[1-9]*) echo "RP_INTERVENED: n2[$O2] n1[$O1]"; exit 0 ;; esac
  case "$O2 $O1" in *s128=[1-9]*) echo "RP_SLEEP128: n2[$O2] n1[$O1]"; exit 0 ;; esac
  sleep 900
done
echo RP_WATCH2_WINDOW_DONE
