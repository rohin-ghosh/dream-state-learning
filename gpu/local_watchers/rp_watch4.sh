#!/bin/bash
# fires when seed401 has its post-brief check (sleep 224) or any other RP life intervenes
S2="/Users/rohing/dream-state/gpu/ovx_ssh.sh"; S1="/Users/rohing/dream-state/gpu/a40_ssh.sh"
for ((i=0; i<60; i++)); do
  O2=$(bash "$S2" 'a=$(test -f ~/v6_out/RP_B_seed401/sleep_0224/parent_brief.json && echo 1 || echo 0); iv=$(grep -l "\"intervened\": true" ~/v6_out/RP_B_seed400/sleep_*/parent_brief.json 2>/dev/null | wc -l); echo "s401_224=$a iv400=$iv"' 2>/dev/null)
  O1=$(bash "$S1" 'iv=$(grep -l "\"intervened\": true" ~/v6_out/RP_B_seed402/sleep_*/parent_brief.json 2>/dev/null | wc -l); echo "iv402=$iv"' 2>/dev/null)
  echo "$(date '+%H:%M') $O2 $O1"
  case "$O2 $O1" in *s401_224=1*|*iv400=[1-9]*|*iv402=[1-9]*) echo "RP_EVENT:$O2 $O1"; exit 0 ;; esac
  sleep 900
done
echo RP_WATCH4_WINDOW_DONE
